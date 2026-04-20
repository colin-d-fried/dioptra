"""add user lockout fields and password history table

Revision ID: 7f3c1b4a9e21
Revises: ad4f89b2288d
Create Date: 2026-04-20 15:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

from dioptra.restapi.db.custom_types import TZDateTime

# revision identifiers, used by Alembic.
revision = "7f3c1b4a9e21"
down_revision = "ad4f89b2288d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "failed_login_attempts",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column("locked_until", TZDateTime(), nullable=True)
        )

    # Drop the server_default after populating existing rows so that the
    # application-level default (0) is the authoritative source.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "failed_login_attempts", server_default=None
        )

    op.create_table(
        "user_password_history",
        sa.Column(
            "password_history_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("created_on", TZDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_user_password_history_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "password_history_id", name=op.f("pk_user_password_history")
        ),
    )
    with op.batch_alter_table("user_password_history", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_user_password_history_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("user_password_history", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_password_history_user_id"))
    op.drop_table("user_password_history")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_login_attempts")
