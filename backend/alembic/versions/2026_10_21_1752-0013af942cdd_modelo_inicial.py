"""modelo inicial

Revision ID: 0013af942cdd
Revises:
Create Date: 2026-10-21 17:52:09.469702

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013af942cdd"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categoria")),
        sa.UniqueConstraint("nombre", name=op.f("uq_categoria_nombre")),
    )
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("correo", sa.Text(), nullable=False),
        sa.Column("clave_hash", sa.Text(), nullable=False),
        sa.Column("rol", sa.Text(), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("rol IN ('ADMIN', 'USUARIO')", name=op.f("ck_usuario_rol")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        sa.UniqueConstraint("correo", name=op.f("uq_usuario_correo")),
    )
    op.create_table(
        "producto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("unidad", sa.Text(), nullable=False),
        sa.Column("precio_compra", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("precio_venta", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("stock", sa.Numeric(precision=12, scale=3), server_default="0", nullable=False),
        sa.Column(
            "stock_minimo", sa.Numeric(precision=12, scale=3), server_default="0", nullable=False
        ),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "unidad IN ('UNIDAD', 'KG', 'LITRO', 'CAJA')", name=op.f("ck_producto_unidad")
        ),
        sa.CheckConstraint("precio_compra >= 0", name=op.f("ck_producto_precio_compra")),
        sa.CheckConstraint("precio_venta >= 0", name=op.f("ck_producto_precio_venta")),
        sa.CheckConstraint("stock >= 0", name=op.f("ck_producto_stock")),
        sa.CheckConstraint("stock_minimo >= 0", name=op.f("ck_producto_stock_minimo")),
        sa.ForeignKeyConstraint(
            ["categoria_id"], ["categoria.id"], name=op.f("fk_producto_categoria_id_categoria")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_producto")),
        sa.UniqueConstraint("codigo", name=op.f("uq_producto_codigo")),
    )
    op.create_table(
        "movimiento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("cantidad", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("stock_despues", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("anula_a", sa.Integer(), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "motivo IN ('COMPRA', 'DEVOLUCION', 'USO', 'VENTA', 'PERDIDA', 'AJUSTE', 'ANULACION')",
            name=op.f("ck_movimiento_motivo"),
        ),
        sa.CheckConstraint("tipo IN ('ENTRADA', 'SALIDA')", name=op.f("ck_movimiento_tipo")),
        sa.CheckConstraint("cantidad > 0", name=op.f("ck_movimiento_cantidad")),
        sa.CheckConstraint("stock_despues >= 0", name=op.f("ck_movimiento_stock_despues")),
        sa.ForeignKeyConstraint(
            ["anula_a"], ["movimiento.id"], name=op.f("fk_movimiento_anula_a_movimiento")
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"], ["producto.id"], name=op.f("fk_movimiento_producto_id_producto")
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name=op.f("fk_movimiento_usuario_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimiento")),
        sa.UniqueConstraint("anula_a", name=op.f("uq_movimiento_anula_a")),
    )
    op.create_index(
        "ix_movimiento_producto_fecha", "movimiento", ["producto_id", "fecha"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_movimiento_producto_fecha", table_name="movimiento")
    op.drop_table("movimiento")
    op.drop_table("producto")
    op.drop_table("usuario")
    op.drop_table("categoria")
