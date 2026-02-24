from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
import uuid


def percent(amount: Decimal, pct: Decimal) -> Decimal:
    return (amount * pct / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def money(value) -> Decimal:
    # Normaliza a 2 decimales tipo moneda (evita floats)
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Product:
    id_code: str
    title: str
    unit_price: Decimal  # precio base (no usar float)


@dataclass
class OrderLine:
    product_id: str
    title: str
    unit_price: Decimal  # snapshot (congelado)
    quantity: int
    currency_id: str = "ARS"

    @classmethod
    def from_product(cls, product: Product, quantity: int, currency_id: str = "ARS") -> "OrderLine":
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return cls(
            product_id=str(product.id_code),
            title=str(product.title),
            unit_price=money(product.unit_price),
            quantity=int(quantity),
            currency_id=str(currency_id),
        )

    def line_total(self) -> Decimal:
        return money(self.unit_price * self.quantity)

    def to_mp_item(self) -> dict:
        # MercadoPago espera unit_price numerico (float/number).
        # Internamente usamos Decimal; convertimos al final.
        return {
            "title": self.title,
            "quantity": self.quantity,
            "currency_id": self.currency_id,
            "unit_price": float(self.unit_price),
        }


class Order:
    VALID_STATUSES = {"pending", "paid", "cancelled", "expired"}

    def __init__(self, order_id: Optional[str] = None, currency_id: str = "ARS"):
        self.id = order_id or str(uuid.uuid4())  # external_reference recomendado
        self.currency_id = currency_id
        self.status = "pending"
        self.lines: Dict[str, OrderLine] = {}  # product_id -> OrderLine

    def add_product(self, product: Product, quantity: int = 1) -> None:
        if self.status != "pending":
            raise RuntimeError("cannot modify order when status is not pending")

        if quantity <= 0:
            raise ValueError("quantity must be positive")

        pid = str(product.id_code)
        if pid in self.lines:
            self.lines[pid].quantity += int(quantity)
        else:
            self.lines[pid] = OrderLine.from_product(product, quantity, currency_id=self.currency_id)

    def decrement_product(self, product_id: str, quantity: int = 1):
        if self.status != "pending":
            raise RuntimeError("cannot modify order when status is not pending")

        if quantity <= 0:
            raise ValueError("quantity must be positive")

        if product_id not in self.lines:
            return

        line = self.lines[product_id]
        line.quantity -= quantity

        if line.quantity <= 0:
            del self.lines[product_id]

    def set_quantity(self, product_id: str, quantity: int) -> None:
        if self.status != "pending":
            raise RuntimeError("cannot modify order when status is not pending")

        if quantity < 0:
            raise ValueError("quantity must be >= 0")

        if quantity == 0:
            self.lines.pop(str(product_id), None)
            return

        if str(product_id) not in self.lines:
            raise KeyError("product not in order")

        self.lines[str(product_id)].quantity = int(quantity)

    def remove_product(self, product_id: str) -> None:
        if self.status != "pending":
            raise RuntimeError("cannot modify order when status is not pending")
        self.lines.pop(str(product_id), None)

    def is_empty(self) -> bool:
        return len(self.lines) == 0

    def total_amount(self) -> Decimal:
        return money(sum((l.line_total() for l in self.lines.values()), Decimal("0")))

    def to_mercadopago_items(self) -> List[dict]:
        return [l.to_mp_item() for l in self.lines.values()]

    def build_mp_preference_payload(
        self,
        payer_email: str,
        success_url: str,
        pending_url: str,
        failure_url: str,
        fee_percent: Decimal | None = None,
    ) -> dict:
        if self.is_empty():
            raise ValueError("order is empty")

        payload = {
            "items": self.to_mercadopago_items(),
            "payer": {"email": payer_email},
            "external_reference": self.id,
            "back_urls": {
                "success": success_url,
                "pending": pending_url,
                "failure": failure_url,
            },
            "auto_return": "approved",
        }

        if fee_percent is not None:
            if fee_percent < 0 or fee_percent > 100:
                raise ValueError("fee_percent must be between 0 and 100")

            total = self.total_amount()
            fee = percent(total, Decimal(fee_percent))
            payload["marketplace_fee"] = float(fee)

        return payload

    def mark_paid(self) -> None:
        self.status = "paid"

    def mark_cancelled(self) -> None:
        self.status = "cancelled"

    def mark_expired(self) -> None:
        self.status = "expired"




# use


# payload listo para POST a /checkout/preferences con el token que corresponda
#order.add_product(p, 2)        -> suma
#order.decrement_product(p, 1)  -> resta
#order.remove_product(p)        -> elimina
#order.set_quantity(p, 5)       -> fija

def use():
    ticket = Product(id_code="ticket_general", title="Entrada evento", unit_price=money("15000"))
    vip = Product(id_code="ticket_vip", title="Entrada evento", unit_price=money("30000"))
    order = Order()
    order.add_product(ticket, 2)
    order.add_product(vip, 1)

    payload = order.build_mp_preference_payload(
        payer_email="buyer@mail.com",
        success_url="https://ok",
        pending_url="https://pending",
        failure_url="https://fail",
        fee_percent=Decimal("10")  # 10%
    )

    print(f"Total amount of the order: {order.total_amount()}")
    print(f"My comission is: {percent(order.total_amount(),10)}")

    print(f"The payload to mp: {payload}")

use()