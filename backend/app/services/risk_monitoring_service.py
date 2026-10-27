import logging

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.attrition_prediction import AttritionPrediction
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.risk_monitoring_event import RiskMonitoringEvent
from app.models.user import User

logger = logging.getLogger(__name__)


def record_risk_event(
    db: Session,
    prediction: AttritionPrediction,
) -> RiskMonitoringEvent | None:
    """Record a prediction event and notify HR when risk enters High."""

    if prediction.employee_id is None:
        logger.info(
            "Skipping risk event: prediction %s has no employee.",
            prediction.id,
        )
        return None

    try:
        existing = db.scalar(
            select(RiskMonitoringEvent).where(
                RiskMonitoringEvent.prediction_id == prediction.id
            )
        )

        if existing is not None:
            return existing

        previous_condition = or_(
            AttritionPrediction.created_at < prediction.created_at,
            and_(
                AttritionPrediction.created_at == prediction.created_at,
                AttritionPrediction.id < prediction.id,
            ),
        )

        previous = db.scalar(
            select(AttritionPrediction)
            .where(
                AttritionPrediction.employee_id == prediction.employee_id,
                previous_condition,
            )
            .order_by(
                AttritionPrediction.created_at.desc(),
                AttritionPrediction.id.desc(),
            )
            .limit(1)
        )

        # Record meaningful score changes even when the risk category stays the same.
        risk_score_change_threshold = 10.0

        if previous is None:
            event_type = "INITIAL_ASSESSMENT"
        elif previous.risk_level != prediction.risk_level:
            if prediction.risk_level == "High":
                event_type = "RISK_ESCALATED"
            elif previous.risk_level == "High":
                event_type = "RISK_REDUCED"
            else:
                event_type = "RISK_CHANGED"
        elif abs(
            float(prediction.risk_score) - float(previous.risk_score)
        ) >= risk_score_change_threshold:
            event_type = "RISK_SCORE_CHANGED"
        else:
            event_type = "ASSESSMENT_UNCHANGED"

        event = RiskMonitoringEvent(
            prediction_id=prediction.id,
            employee_id=prediction.employee_id,
            previous_risk_level=previous.risk_level if previous else None,
            current_risk_level=prediction.risk_level,
            previous_risk_score=previous.risk_score if previous else None,
            current_risk_score=prediction.risk_score,
            event_type=event_type,
            triggered_by=prediction.created_by,
        )

        db.add(event)
        db.flush()

        should_alert = (
            prediction.risk_level == "High"
            and (previous is None or previous.risk_level != "High")
        )

        if should_alert:
            employee = db.get(Employee, prediction.employee_id)
            employee_name = (
                employee.full_name
                if employee and employee.full_name
                else f"Employee ID {prediction.employee_id}"
            )

            # Stored risk scores already use the 0-100 percentage scale.
            risk_percentage = float(prediction.risk_score)

            recipients = db.scalars(
                select(User).where(
                    User.is_active.is_(True),
                    User.role.in_(("ADMIN", "HR")),
                )
            ).all()

            for recipient in recipients:
                db.add(
                    Notification(
                        user_id=recipient.id,
                        title="High attrition risk detected",
                        message=(
                            f"{employee_name} has a High attrition-risk "
                            f"prediction ({risk_percentage:.1f}%). "
                            "Please review the assessment and consider "
                            "appropriate employee support."
                        ),
                        category="AI_RISK",
                        is_read=False,
                    )
                )

            logger.info(
                "High-risk alert prepared for employee %s; "
                "%s recipient(s).",
                prediction.employee_id,
                len(recipients),
            )

        db.commit()
        db.refresh(event)

        logger.info(
            "Risk event %s recorded for prediction %s: %s",
            event.id,
            prediction.id,
            event_type,
        )
        return event

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error recording risk event for prediction %s.",
            prediction.id,
        )
        raise

    except Exception:
        db.rollback()
        logger.exception(
            "Unexpected error recording risk event for prediction %s.",
            prediction.id,
        )
        raise
