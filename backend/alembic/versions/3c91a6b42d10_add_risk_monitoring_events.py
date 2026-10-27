"""Add risk monitoring events.

Revision ID: 3c91a6b42d10
Revises: 2b48251d657b
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "3c91a6b42d10"
down_revision: Union[str, Sequence[str], None] = "2b48251d657b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_monitoring_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("previous_risk_level", sa.String(20), nullable=True),
        sa.Column("current_risk_level", sa.String(20), nullable=False),
        sa.Column("previous_risk_score", sa.Float(), nullable=True),
        sa.Column("current_risk_score", sa.Float(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("triggered_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["prediction_id"], ["attrition_predictions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"], ["employees.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["triggered_by"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "prediction_id",
            name="uq_risk_monitoring_events_prediction_id",
        ),
    )
    op.create_index(
        "ix_risk_monitoring_events_employee_id",
        "risk_monitoring_events",
        ["employee_id"],
    )
    op.create_index(
        "ix_risk_monitoring_events_created_at",
        "risk_monitoring_events",
        ["created_at"],
    )
    op.create_index(
        "ix_risk_events_employee_created",
        "risk_monitoring_events",
        ["employee_id", "created_at"],
    )
    op.create_index(
        "ix_risk_events_event_type",
        "risk_monitoring_events",
        ["event_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_risk_events_event_type", table_name="risk_monitoring_events")
    op.drop_index("ix_risk_events_employee_created", table_name="risk_monitoring_events")
    op.drop_index("ix_risk_monitoring_events_created_at", table_name="risk_monitoring_events")
    op.drop_index("ix_risk_monitoring_events_employee_id", table_name="risk_monitoring_events")
    op.drop_table("risk_monitoring_events")
