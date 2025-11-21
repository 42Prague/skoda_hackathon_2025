"""Add Škoda dataset columns v2

Revision ID: skoda_columns_v2
Revises: skoda_fields_001
Create Date: 2025-11-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "skoda_columns_v2"
down_revision = "skoda_fields_001"
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema upgrades."""
    op.add_column(
        "employee_record",
        sa.Column("ob_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("employee_record", sa.Column("education_branch_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("education_branch_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("education_branch_group_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("education_branch_group_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("education_category_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("education_category_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("field_of_study_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("field_of_study_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("field_of_study_code", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("coordinator_group_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("planned_profession_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("planned_profession_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("planned_position_id", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("planned_position_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("hr_contact_name", sa.String(length=255), nullable=True))
    op.add_column("employee_record", sa.Column("pers_profession_name", sa.String(length=255), nullable=True))

    op.add_column("learning_history", sa.Column("content_id", sa.String(length=255), nullable=True))
    op.add_column("learning_history", sa.Column("content_url", sa.String(length=500), nullable=True))
    op.add_column("learning_history", sa.Column("course_type", sa.String(length=255), nullable=True))
    op.add_column("learning_history", sa.Column("verified_minutes", sa.Integer(), nullable=True))
    op.add_column("learning_history", sa.Column("estimated_minutes", sa.Integer(), nullable=True))
    op.add_column("learning_history", sa.Column("verified", sa.Boolean(), nullable=True))
    op.add_column("learning_history", sa.Column("completion_points", sa.Float(), nullable=True))
    op.add_column("learning_history", sa.Column("user_rating", sa.Float(), nullable=True))

    op.add_column("qualification_record", sa.Column("fm_number", sa.String(length=255), nullable=True))

    op.add_column("org_hierarchy_record", sa.Column("node_id", sa.String(length=255), nullable=True))
    op.add_column("org_hierarchy_record", sa.Column("parent_node_id", sa.String(length=255), nullable=True))
    op.add_column("org_hierarchy_record", sa.Column("short_code", sa.String(length=255), nullable=True))
    op.add_column("org_hierarchy_record", sa.Column("description", sa.String(length=500), nullable=True))


def downgrade():
    """Revert schema upgrades."""
    op.drop_column("org_hierarchy_record", "description")
    op.drop_column("org_hierarchy_record", "short_code")
    op.drop_column("org_hierarchy_record", "parent_node_id")
    op.drop_column("org_hierarchy_record", "node_id")

    op.drop_column("qualification_record", "fm_number")

    op.drop_column("learning_history", "user_rating")
    op.drop_column("learning_history", "completion_points")
    op.drop_column("learning_history", "verified")
    op.drop_column("learning_history", "estimated_minutes")
    op.drop_column("learning_history", "verified_minutes")
    op.drop_column("learning_history", "course_type")
    op.drop_column("learning_history", "content_url")
    op.drop_column("learning_history", "content_id")

    op.drop_column("employee_record", "pers_profession_name")
    op.drop_column("employee_record", "hr_contact_name")
    op.drop_column("employee_record", "planned_position_name")
    op.drop_column("employee_record", "planned_position_id")
    op.drop_column("employee_record", "planned_profession_name")
    op.drop_column("employee_record", "planned_profession_id")
    op.drop_column("employee_record", "coordinator_group_id")
    op.drop_column("employee_record", "field_of_study_code")
    op.drop_column("employee_record", "field_of_study_name")
    op.drop_column("employee_record", "field_of_study_id")
    op.drop_column("employee_record", "education_category_name")
    op.drop_column("employee_record", "education_category_id")
    op.drop_column("employee_record", "education_branch_group_name")
    op.drop_column("employee_record", "education_branch_group_id")
    op.drop_column("employee_record", "education_branch_name")
    op.drop_column("employee_record", "education_branch_id")
    op.drop_column("employee_record", "ob_codes")

