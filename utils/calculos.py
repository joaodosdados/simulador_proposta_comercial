"""
Motor de cálculo financeiro — CostWise AI.

Taxas e constantes carregadas de config.json (não versionado).
NPV GP%: desconto mensal exato (WACC anual → mensal).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

# ── Carrega configuração sensível ──────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
if not _CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"Arquivo de configuração não encontrado: {_CONFIG_PATH}\n"
        "Copie config.example.json → config.json e preencha com os valores reais."
    )

with open(_CONFIG_PATH, encoding="utf-8") as _f:
    _CFG = json.load(_f)

# ── Constantes financeiras (de config.json) ────────────────────────────────────
WACC_ANUAL = _CFG["wacc_anual"]
WACC_MENSAL = (1 + WACC_ANUAL) ** (1 / 12) - 1
CONTINGENCIA = _CFG["contingencia_default"]
ISS = _CFG["iss"]
PIS_COFINS = _CFG["pis_cofins"]
IMPOSTOS_TOTAL = ISS + PIS_COFINS
NPV_GP_MINIMO = _CFG["npv_gp_minimo"]
REVENUE_APPORTIONMENT_PCT = _CFG["revenue_apportionment_pct"]
HORAS_MES_DEFAULT = _CFG["horas_mes_default"]
HORAS_MES = HORAS_MES_DEFAULT
PAYMENT_TERMS_DEFAULT = _CFG["payment_terms_default"]


def set_horas_mes(valor: float) -> None:
    """Atualiza o valor de HORAS_MES usado em todos os cálculos."""
    global HORAS_MES
    HORAS_MES = valor


# ── Tabela de Contingência (Risk Profile × Work Type) ─────────────────────────
CONTINGENCY_TABLE: dict[str, dict[str, float]] = _CFG["contingency_table"]
RISK_PROFILES = list(CONTINGENCY_TABLE.keys())
WORK_TYPES = {
    "I": "Staff Aug / Consulting",
    "II": "Support Svcs / Process Mgmt",
    "III": "Projects",
}


# ── Taxas por banda (BRL/hora) — de config.json ──────────────────────────────
TAXAS_BANDA: dict[str, float] = _CFG["taxas_banda"]

BANDAS = list(TAXAS_BANDA.keys())


# ── Modelos de dados ───────────────────────────────────────────────────────────
@dataclass
class Profissional:
    nome: str
    banda: str
    meses: list[float] = field(default_factory=lambda: [0.0] * 12)

    @property
    def taxa_hora(self) -> float:
        return TAXAS_BANDA.get(self.banda, 0.0)

    @property
    def total_horas(self) -> float:
        return sum(u * HORAS_MES for u in self.meses)

    @property
    def total_base_cost(self) -> float:
        return self.total_horas * self.taxa_hora

    def to_dict(self) -> dict:
        return {"nome": self.nome, "banda": self.banda, "meses": self.meses}

    @classmethod
    def from_dict(cls, d: dict) -> "Profissional":
        return cls(nome=d["nome"], banda=d["banda"], meses=d.get("meses", [0.0] * 12))


@dataclass
class Grupo:
    nome: str
    profissionais: list[Profissional] = field(default_factory=list)

    @property
    def total_horas(self) -> float:
        return sum(p.total_horas for p in self.profissionais)

    @property
    def total_base_cost(self) -> float:
        return sum(p.total_base_cost for p in self.profissionais)

    def to_dict(self) -> dict:
        return {
            "nome": self.nome,
            "profissionais": [p.to_dict() for p in self.profissionais],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Grupo":
        return cls(
            nome=d["nome"],
            profissionais=[
                Profissional.from_dict(p) for p in d.get("profissionais", [])
            ],
        )


@dataclass
class ItemMisc:
    """Item de despesa avulsa (viagens, licenças, etc.)."""

    descricao: str
    quantidade: int = 1
    valor_unitario: float = 0.0

    @property
    def total(self) -> float:
        return self.quantidade * self.valor_unitario

    def to_dict(self) -> dict:
        return {
            "descricao": self.descricao,
            "quantidade": self.quantidade,
            "valor_unitario": self.valor_unitario,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMisc":
        return cls(
            descricao=d.get("descricao", ""),
            quantidade=d.get("quantidade", 1),
            valor_unitario=d.get("valor_unitario", 0.0),
        )


# ── Billing Schedule ───────────────────────────────────────────────────────────
BILLING_MODES = {
    "cost": "Proporcional ao Custo",
    "equal": "Igualitário (igual por mês)",
    "custom": "Customizado",
}


def billing_mensal(
    mode: str,
    n_meses: int,
    net_price_total: float,
    bc_mensal: list[float],
    custom_pesos: list[float] | None = None,
) -> list[float]:
    """Retorna a receita (Net Price) de cada mês conforme o billing schedule.

    - cost:   proporcional ao base cost mensal
    - equal:  dividido igualmente entre meses ativos
    - custom: usa pesos fornecidos (% do net price por mês)
    """
    if net_price_total == 0 or n_meses == 0:
        return [0.0] * n_meses

    if mode == "equal":
        meses_ativos = sum(1 for bc in bc_mensal if bc > 0) or n_meses
        per_month = net_price_total / meses_ativos
        return [per_month if bc_mensal[m] > 0 else 0.0 for m in range(n_meses)]

    if mode == "custom" and custom_pesos and len(custom_pesos) >= n_meses:
        total_peso = sum(custom_pesos[:n_meses]) or 1.0
        return [net_price_total * custom_pesos[m] / total_peso for m in range(n_meses)]

    # default: proporcional ao custo ("cost")
    total_bc = sum(bc_mensal) or 1.0
    return [net_price_total * bc / total_bc for bc in bc_mensal]


# ── Cálculos financeiros ──────────────────────────────────────────────────────
def _base_cost_mensal(grupos: list[Grupo], n_meses: int) -> list[float]:
    bc = [0.0] * n_meses
    for g in grupos:
        for p in g.profissionais:
            taxa = p.taxa_hora
            for m in range(min(n_meses, len(p.meses))):
                bc[m] += p.meses[m] * HORAS_MES * taxa
    return bc


def _custo_mensal_com_misc(bc_mensal: list[float], misc_total: float) -> list[float]:
    """Adiciona misc distribuído entre meses ativos ao base-cost mensal."""
    n = len(bc_mensal)
    meses_ativos = sum(1 for bc in bc_mensal if bc > 0) or n
    misc_m = misc_total / meses_ativos
    return [bc + (misc_m if bc > 0 else 0.0) for bc in bc_mensal]


def calcular_npv_gp(
    grupos: list[Grupo],
    markup: float,
    n_meses: int,
    wacc_mensal: float = WACC_MENSAL,
    contingencia: float = CONTINGENCIA,
    misc_total: float = 0.0,
    billing_mode: str = "cost",
    billing_custom: list[float] | None = None,
) -> float:
    bc_mensal = _base_cost_mensal(grupos, n_meses)
    custo_m = _custo_mensal_com_misc(bc_mensal, misc_total)
    total_base = sum(custo_m)
    net_price_total = total_base * markup

    # Receita segue billing schedule, custo segue staffing plan
    receita_m = billing_mensal(
        billing_mode, n_meses, net_price_total, custo_m, billing_custom
    )

    npv_receita = 0.0
    npv_custo = 0.0
    for m in range(n_meses):
        fator = 1.0 / (1 + wacc_mensal) ** (m + 1)
        npv_receita += receita_m[m] * fator
        npv_custo += custo_m[m] * (1 + contingencia) * fator
    if npv_receita == 0:
        return 0.0
    return (npv_receita - npv_custo) / npv_receita


def calcular_markup_minimo(
    grupos: list[Grupo],
    n_meses: int,
    npv_gp_alvo: float = NPV_GP_MINIMO,
    contingencia: float = CONTINGENCIA,
    misc_total: float = 0.0,
    billing_mode: str = "cost",
    billing_custom: list[float] | None = None,
) -> float:
    lo, hi = 1.0, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if (
            calcular_npv_gp(
                grupos,
                mid,
                n_meses,
                contingencia=contingencia,
                misc_total=misc_total,
                billing_mode=billing_mode,
                billing_custom=billing_custom,
            )
            < npv_gp_alvo
        ):
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def calcular_summary(
    grupos: list[Grupo],
    markup: float,
    n_meses: int,
    contingencia: float = CONTINGENCIA,
    misc_total: float = 0.0,
    billing_mode: str = "cost",
    billing_custom: list[float] | None = None,
) -> dict:
    total_horas = sum(g.total_horas for g in grupos)
    total_base_cost = sum(g.total_base_cost for g in grupos) + misc_total
    total_cost = total_base_cost * (1 + contingencia)
    net_price = total_base_cost * markup
    total_tcv = net_price / (1 - IMPOSTOS_TOTAL) if total_horas > 0 else 0
    npv_gp = calcular_npv_gp(
        grupos,
        markup,
        n_meses,
        contingencia=contingencia,
        misc_total=misc_total,
        billing_mode=billing_mode,
        billing_custom=billing_custom,
    )
    markup_min = (
        calcular_markup_minimo(
            grupos,
            n_meses,
            contingencia=contingencia,
            misc_total=misc_total,
            billing_mode=billing_mode,
            billing_custom=billing_custom,
        )
        if total_horas > 0
        else 0
    )
    taxa_hora = total_tcv / total_horas if total_horas > 0 else 0

    return {
        "total_horas": total_horas,
        "total_base_cost": total_base_cost,
        "total_cost": total_cost,
        "net_price": net_price,
        "total_tcv": total_tcv,
        "markup": markup,
        "markup_min": markup_min,
        "taxa_hora": taxa_hora,
        "npv_gp": npv_gp,
        "npv_gp_ok": npv_gp >= NPV_GP_MINIMO,
        "misc_total": misc_total,
    }


def summary_por_grupo(
    grupos: list[Grupo],
    markup: float,
    n_meses: int,
    misc_total: float = 0.0,
) -> list[dict]:
    total_bc = sum(g.total_base_cost for g in grupos) + misc_total or 1
    rows = []
    for g in grupos:
        horas = g.total_horas
        bc = g.total_base_cost
        tcv = (bc * markup) / (1 - IMPOSTOS_TOTAL) if horas > 0 else 0
        th = tcv / horas if horas > 0 else 0
        rows.append(
            {
                "grupo": g.nome,
                "horas": horas,
                "base_cost": bc,
                "base_pct": bc / total_bc,
                "tcv": tcv,
                "markup": markup if horas > 0 else 0,
                "taxa_hora": th,
            }
        )
    # Adiciona linha Miscellaneous se houver
    if misc_total > 0:
        misc_tcv = (misc_total * markup) / (1 - IMPOSTOS_TOTAL)
        rows.append(
            {
                "grupo": "Miscellaneous",
                "horas": 0,
                "base_cost": misc_total,
                "base_pct": misc_total / total_bc,
                "tcv": misc_tcv,
                "markup": markup,
                "taxa_hora": 0,
            }
        )
    return rows


# ── Preliminary P&L ───────────────────────────────────────────────────────────
def calcular_pnl(
    grupos: list[Grupo],
    markup: float,
    n_meses: int,
    exch_rate: float = 5.50325,
    contingencia: float = CONTINGENCIA,
    misc_total: float = 0.0,
    billing_mode: str = "cost",
    billing_custom: list[float] | None = None,
) -> dict:
    """Retorna o Preliminary P&L completo no padrão da aba Summary."""
    base_cost = sum(g.total_base_cost for g in grupos) + misc_total
    total_horas = sum(g.total_horas for g in grupos)

    # Receita
    net_price = base_cost * markup
    sales_taxes_pct = IMPOSTOS_TOTAL
    tcv = net_price / (1 - sales_taxes_pct) if total_horas > 0 else 0
    revenue = net_price  # sem penalty contingency

    # Custos
    risk_contingency = base_cost * contingencia
    risk_contingency_pct = contingencia
    total_cost = base_cost + risk_contingency

    # Nominal
    nominal_gp = revenue - total_cost
    nominal_gp_pct = nominal_gp / revenue if revenue else 0

    rev_apportionment = revenue * REVENUE_APPORTIONMENT_PCT
    rev_apportionment_pct = REVENUE_APPORTIONMENT_PCT

    nominal_pti = nominal_gp - rev_apportionment
    nominal_pti_pct = nominal_pti / revenue if revenue else 0

    # NPV (com desconto WACC mensal) — receita segue billing schedule
    bc_mensal = _base_cost_mensal(grupos, n_meses)
    custo_m_vec = _custo_mensal_com_misc(bc_mensal, misc_total)
    receita_m_vec = billing_mensal(
        billing_mode, n_meses, net_price, custo_m_vec, billing_custom
    )

    npv_receita = 0.0
    npv_custo = 0.0
    npv_rev_app = 0.0
    for m in range(n_meses):
        fator = 1.0 / (1 + WACC_MENSAL) ** (m + 1)
        npv_receita += receita_m_vec[m] * fator
        npv_custo += custo_m_vec[m] * (1 + contingencia) * fator
        npv_rev_app += receita_m_vec[m] * REVENUE_APPORTIONMENT_PCT * fator

    npv_gp = npv_receita - npv_custo
    npv_gp_pct = npv_gp / npv_receita if npv_receita else 0
    npv_pti = npv_gp - npv_rev_app
    npv_pti_pct = npv_pti / npv_receita if npv_receita else 0

    # Contract GP (excl. TVM & Contingency)
    contract_gp = revenue - base_cost
    contract_gp_pct = contract_gp / revenue if revenue else 0

    return {
        # header
        "exch_rate": exch_rate,
        # TCV / receita
        "tcv": tcv,
        "sales_taxes_pct": sales_taxes_pct,
        "net_price": net_price,
        "revenue": revenue,
        # custos
        "base_cost": base_cost,
        "risk_contingency": risk_contingency,
        "risk_contingency_pct": risk_contingency_pct,
        "total_cost": total_cost,
        # nominal
        "nominal_gp": nominal_gp,
        "nominal_gp_pct": nominal_gp_pct,
        "rev_apportionment": rev_apportionment,
        "rev_apportionment_pct": rev_apportionment_pct,
        "nominal_pti": nominal_pti,
        "nominal_pti_pct": nominal_pti_pct,
        # NPV
        "npv_gp": npv_gp,
        "npv_gp_pct": npv_gp_pct,
        "npv_pti": npv_pti,
        "npv_pti_pct": npv_pti_pct,
        # contract GP
        "contract_gp": contract_gp,
        "contract_gp_pct": contract_gp_pct,
        # totais
        "total_horas": total_horas,
    }
