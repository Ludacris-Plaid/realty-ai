"""Regulatory MCP — Comprehensive Canada + US real estate law reference.

Structured as a queryable knowledge base with citations.
Integrated into Athena's tool system for natural-language compliance queries.
"""
from __future__ import annotations

import re
import json
from typing import Optional

# ─── CANADA REGULATORY FRAMEWORK ────────────────────────────────────────────

CANADA_REGULATIONS = {
    "federal": {
        "proceeds_of_crime": {
            "title": "Proceeds of Crime (Money Laundering) and Terrorist Financing Act",
            "body": "Real estate brokers and sales representatives are reporting entities under FINTRAC. Must verify client identity, keep records for 5 years, and report suspicious transactions and large cash transactions > $10,000 CAD.",
            "jurisdiction": "Federal (Canada)",
            "citations": ["PCMLTFA", "FINTRAC Guidelines for Real Estate"],
            "keywords": ["fintrac", "anti-money laundering", "aml", "identity verification", "record keeping", "suspicious transaction"],
        },
        "competition_act": {
            "title": "Competition Act (Canada)",
            "body": "Prohibits false or misleading representations in real estate advertising, including price representations that don't reflect all costs. Must not make representations to the public without proper substantiation.",
            "jurisdiction": "Federal (Canada)",
            "citations": ["Competition Act, RSC 1985, c C-34"],
            "keywords": ["advertising", "misleading", "false representation", "competition"],
        },
        "pipeda": {
            "title": "Personal Information Protection and Electronic Documents Act (PIPEDA)",
            "body": "Governs how real estate brokerages collect, use, and disclose personal information. Requires consent for collection, limits use to identified purposes, and mandates security safeguards. Applies in provinces without substantially similar privacy legislation.",
            "jurisdiction": "Federal (Canada)",
            "citations": ["PIPEDA, SC 2000, c 5"],
            "keywords": ["privacy", "personal information", "data protection", "consent", "piperda"],
        },
        "criminal_code_fraud": {
            "title": "Criminal Code — Fraud and Forged Documents",
            "body": "Section 380 makes real estate fraud (mortgage fraud, identity theft in transactions) a criminal offence punishable by up to 14 years imprisonment. Includes falsification of documents, income, or down payment sources.",
            "jurisdiction": "Federal (Canada)",
            "citations": ["Criminal Code, RSC 1985, c C-46, s 380"],
            "keywords": ["fraud", "mortgage fraud", "forgery", "criminal", "identity theft"],
        },
    },
    "ontario": {
        "reco": {
            "title": "Real Estate Council of Ontario (RECO) — Code of Ethics",
            "body": "All Ontario real estate salespersons and brokerages must be registered with RECO. The Code of Ethics requires: fair dealing, best interests of clients, disclosure of material facts, confidentiality, and continuous education. RECO administers the Real Estate and Business Brokers Act (REBBA). Mandatory errors and omissions insurance.",
            "jurisdiction": "Ontario",
            "citations": ["REBBA 2002, SO 2002, c 30", "RECO Code of Ethics"],
            "keywords": ["reco", "rebba", "registration", "ethics", "errors and omissions", "education"],
        },
        "oreb": {
            "title": "Toronto Regional Real Estate Board (TRREB) Rules",
            "body": "TRREB (formerly TREB) governs MLS use in the Greater Toronto Area. Members must comply with board bylaws, MLS rules, and cooperate with other members. TRREB v. Commissioner of Competition (2018 SCC 23) established that real estate board data must be publicly accessible.",
            "jurisdiction": "Ontario (GTA)",
            "citations": ["TRREB Bylaws", "TRREB v Commissioner of Competition, 2018 SCC 23"],
            "keywords": ["trreb", "treb", "toronto", "mls", "data", "competition"],
        },
        "disclosure_ontario": {
            "title": "Seller Property Information Statement (SPIS)",
            "body": "While SPIS (Seller Property Information Statement) is commonly used in Ontario, it is voluntary — not legally required. However, sellers must disclose material latent defects (hidden problems) known to them. Failure to disclose can lead to lawsuits for negligent misrepresentation or fraudulent concealment.",
            "jurisdiction": "Ontario",
            "citations": ["OREA Standard Forms", "Common Law — Duty to Disclose"],
            "keywords": ["spis", "disclosure", "latent defects", "material", "seller", "representation"],
        },
        "cooling_off": {
            "title": "Cooling-Off Period — Ontario",
            "body": "Ontario has NO general cooling-off period for residential real estate purchases once an Agreement of Purchase and Sale is signed. The only exception is for certain pre-construction condominium purchases (10-day cooling-off period under the Condominium Act).",
            "jurisdiction": "Ontario",
            "citations": ["Condominium Act, 1998, SO 1998, c 19"],
            "keywords": ["cooling off", "rescission", "condominium", "pre-construction", "cancellation"],
        },
        "foreign_buyer_ontario": {
            "title": "Non-Resident Speculation Tax (NRST)",
            "body": "Ontario's NRST imposes a 25% tax on the purchase of residential property in Ontario's Greater Golden Horseshoe Region by foreign entities. Certain exemptions: nominees for refugees, protected persons, spouses/spousal equivalents, and international students (after certain period).",
            "jurisdiction": "Ontario",
            "citations": ["Ontario Non-Resident Speculation Tax Act, 2017", "Land Transfer Tax Act"],
            "keywords": ["nrst", "foreign buyer", "non-resident", "speculation tax", "land transfer tax", "foreign entity"],
        },
    },
    "british_columbia": {
        "bc_financial_services": {
            "title": "BC Financial Services Authority (BCFSA)",
            "body": "BCFSA regulates real estate in BC under the Real Estate Services Act (RESA). Requires licensing for all agents and brokerages. Mandatory continuing education, designated agency rules, and disclosure of remuneration.",
            "jurisdiction": "British Columbia",
            "citations": ["Real Estate Services Act, SBC 2004, c 42", "BCFSA Rules"],
            "keywords": ["bcfsa", "resa", "licensing", "bc", "vancouver"],
        },
        "foreign_buyer_bc": {
            "title": "BC Foreign Buyer Tax & Speculation Tax",
            "body": "BC imposes a 20% additional property transfer tax on foreign entities purchasing residential property in specified regions (Metro Vancouver, Fraser Valley, Capital Regional District, etc.). Additionally, a speculation and vacancy tax applies to residential properties in designated areas at 0.5%-2% of assessed value.",
            "jurisdiction": "British Columbia",
            "citations": ["Property Transfer Tax Act, SBC 1996", "Speculation and Vacancy Tax Act, SBC 2018"],
            "keywords": ["foreign buyer", "bc", "property transfer tax", "speculation tax", "vacancy tax", "vancouver"],
        },
        "bc_disclosure": {
            "title": "BC Property Disclosure Statement (PDS)",
            "body": "BC's Property Disclosure Statement is standard practice, completed by the seller. Unlike Ontario's voluntary SPIS, the BC PDS is almost universally used and carries legal weight. Intentional misrepresentation or failure to disclose known defects can result in lawsuit for damages or recission.",
            "jurisdiction": "British Columbia",
            "citations": ["BC Financial Services Authority Guidelines"],
            "keywords": ["pds", "property disclosure", "bc", "defects", "seller"],
        },
    },
    "alberta": {
        "reca": {
            "title": "Real Estate Council of Alberta (RECA)",
            "body": "RECA regulates real estate in Alberta under the Real Estate Act. Administers licensing, investigations, discipline, and mandatory continuing education. RECA enforces the Real Estate Act Rules and Code of Conduct.",
            "jurisdiction": "Alberta",
            "citations": ["Real Estate Act, RSA 2000, c R-5", "RECA Rules"],
            "keywords": ["reca", "alberta", "licensing", "real estate act", "calgary", "edmonton"],
        },
        "ab_disclosure": {
            "title": "Alberta Property Condition Disclosure Statement",
            "body": "Alberta uses a Property Condition Disclosure Statement (PCDS) completed by the seller. It is the standard form in Alberta real estate transactions. The seller must disclose known material defects. Non-disclosure or misrepresentation can void the contract.",
            "jurisdiction": "Alberta",
            "citations": ["Alberta Real Estate Act", "AREA Standard Forms"],
            "keywords": ["pcds", "disclosure", "alberta", "seller", "condition"],
        },
    },
    "quebec": {
        "oaciq": {
            "title": "Organisme d'autoréglementation du courtage immobilier du Québec (OACIQ)",
            "body": "OACIQ regulates real estate brokerage in Quebec under the Real Estate Brokerage Act. All brokers and agencies must hold a licence from OACIQ. Quebec has distinct civil law system (Civil Code of Quebec) affecting real estate transactions, including unique rules on promises to purchase and brokerage contracts.",
            "jurisdiction": "Quebec",
            "citations": ["Real Estate Brokerage Act, CQLR c C-73.1", "Civil Code of Quebec"],
            "keywords": ["oaciq", "quebec", "brokerage", "civil code", "montreal"],
        },
        "quebec_disclosure": {
            "title": "Quebec Seller's Declaration",
            "body": "Quebec uses a mandatory Seller's Declaration (Déclaration du vendeur) form. The seller must complete it truthfully, disclosing all known defects, and it becomes a warranty in the deed of sale. Quebec law provides strong buyer protections — the seller's declaration is a legal warranty against latent defects.",
            "jurisdiction": "Quebec",
            "citations": ["Civil Code of Quebec, CCQ-1991, Art 1726", "OACIQ Rules"],
            "keywords": ["quebec declaration", "seller", "latent defects", "warranty", "civil code"],
        },
    },
    "general_canada": {
        "mortgage_rules": {
            "title": "Canadian Mortgage Rules (OSFI / CMHC)",
            "body": "Mortgage regulations include: minimum down payment (5% for first $500k, 10% for $500k-$1M, 20% over $1M); mortgage stress test for insured and uninsured mortgages (qualify at contract rate + 2% or 5.25%, whichever is higher); 30-year amortization maximum for insured mortgages; CMHC insurance required for down payments under 20%.",
            "jurisdiction": "National (Canada)",
            "citations": ["OSFI Guideline B-20", "CMHC Insurance Requirements", "Bank Act"],
            "keywords": ["mortgage", "down payment", "stress test", "osfi", "cmhc", "amortization", "insured"],
        },
        "mls_rules": {
            "title": "Canadian MLS Rules & CREA",
            "body": "The Canadian Real Estate Association (CREA) governs MLS in Canada. Members must abide by CREA bylaws and MLS rules. Key rules: mandatory cooperation between brokers, clear cooperation rules, data accuracy, and compliance with Competition Act. CREA DDF (Data Distribution Facility) enables data sharing.",
            "jurisdiction": "National (Canada)",
            "citations": ["CREA Bylaws & MLS Rules", "Competition Act"],
            "keywords": ["crea", "mls", "cooperation", "ddf", "data distribution"],
        },
        "gst_hst": {
            "title": "GST/HST on Real Estate (Canada)",
            "body": "GST/HST applies to: newly constructed or substantially renovated homes (GST new housing rebate available); commercial real estate; and deemed supplies under self-supply rules. Resale of used residential property is generally exempt. Provincial harmonization varies (HST in ON, NS, NB, NL; GST only in AB, BC, SK, MB, QC, YT, NT, NU).",
            "jurisdiction": "National (Canada)",
            "citations": ["Excise Tax Act, RSC 1985, c E-15", "CRA GST/HST Memoranda"],
            "keywords": ["gst", "hst", "new housing rebate", "tax", "commercial", "exempt"],
        },
        "tarion": {
            "title": "Tarion Warranty Corporation (Ontario New Home Warranties)",
            "body": "Tarion administers the Ontario New Home Warranties Plan Act. All new homes in Ontario must be enrolled with Tarion. Coverage includes: 1-year warranty on work/materials, 2-year warranty on major systems (electrical, plumbing, heating), 7-year warranty on major structural defects. Builders must be registered with Tarion.",
            "jurisdiction": "Ontario (similar programs exist in BC, Alberta, Quebec)",
            "citations": ["Ontario New Home Warranties Plan Act, RSO 1990, c O.1"],
            "keywords": ["tarion", "new home warranty", "builder", "structural defect", "ontario"],
        },
    },
}

# ─── USA REGULATORY FRAMEWORK ───────────────────────────────────────────────

USA_REGULATIONS = {
    "federal": {
        "respa": {
            "title": "Real Estate Settlement Procedures Act (RESPA)",
            "body": "RESPA (12 USC § 2601-2617) governs the home buying/settlement process. Requires: Good Faith Estimate (GFE) of closing costs; HUD-1 Settlement Statement itemizing all charges; prohibition on kickbacks and referral fees (Section 8); anti-steering rules; escrow account management; and Servicing Transfer disclosures. Enforced by CFPB.",
            "jurisdiction": "Federal (USA)",
            "citations": ["RESPA, 12 USC § 2601-2617", "Regulation X, 12 CFR Part 1024"],
            "keywords": ["respa", "settlement", "closing", "hud", "cfpb", "kickback", "gfe", "referral fee"],
        },
        "tila": {
            "title": "Truth in Lending Act (TILA) / TRID",
            "body": "TILA (15 USC § 1601-1667f) requires clear disclosure of credit terms to consumers. The TILA-RESPA Integrated Disclosure (TRID) rule combines TILA and RESPA disclosures into: Loan Estimate (within 3 business days of application) and Closing Disclosure (3 business days before closing). Requires Annual Percentage Rate (APR) disclosure, finance charge, and right of rescission for certain loans (3 business days).",
            "jurisdiction": "Federal (USA)",
            "citations": ["TILA, 15 USC § 1601", "Regulation Z, 12 CFR Part 1026", "TRID Rule"],
            "keywords": ["tila", "trid", "loan estimate", "closing disclosure", "apr", "right of rescission", "cfpb"],
        },
        "fair_housing": {
            "title": "Fair Housing Act (FHA)",
            "body": "The Fair Housing Act (42 USC § 3601-3631) prohibits discrimination in housing based on race, color, religion, sex (including sexual orientation and gender identity), national origin, familial status, or disability. Applies to: sale/rental of housing, mortgage lending, advertising, and appraisal. Requires reasonable accommodations for disabilities. Enforced by HUD and DOJ.",
            "jurisdiction": "Federal (USA)",
            "citations": ["Fair Housing Act, 42 USC § 3601-3631", "Title VIII of Civil Rights Act of 1968"],
            "keywords": ["fair housing", "discrimination", "fha", "hud", "protected class", "reasonable accommodation", "disability"],
        },
        "adia": {
            "title": "Americans with Disabilities Act (ADA) — Public Accommodations",
            "body": "Title III of the ADA (42 USC § 12181-12189) requires that places of public accommodation (including real estate offices, model homes, and leasing offices) be accessible to individuals with disabilities. Applies to commercial facilities but NOT to private residential housing. Requires barrier removal when readily achievable.",
            "jurisdiction": "Federal (USA)",
            "citations": ["ADA, 42 USC § 12181", "28 CFR Part 36"],
            "keywords": ["ada", "disability", "accessibility", "public accommodation", "barrier removal"],
        },
        "fincen": {
            "title": "FinCEN — Anti-Money Laundering (AML) for Real Estate",
            "body": "FinCEN requires certain real estate professionals to report cash transactions over $10,000 and suspicious activities. Geographic Targeting Orders (GTOs) require title insurance companies to identify beneficial owners behind legal entities purchasing residential property in certain metro areas (NYC, Miami, LA, SF, etc.) for all-cash transactions over $300,000.",
            "jurisdiction": "Federal (USA)",
            "citations": ["Bank Secrecy Act, 31 USC § 5311", "FinCEN GTOs", "31 CFR Chapter X"],
            "keywords": ["finCEN", "aml", "beneficial ownership", "gto", "cash transaction", "suspicious activity"],
        },
        "cfpb": {
            "title": "Consumer Financial Protection Bureau (CFPB) Rules",
            "body": "CFPB has broad authority over consumer financial products and services, including mortgage lending and servicing. Key regulations: Ability-to-Repay / Qualified Mortgage (ATR/QM) rule requiring lenders to verify borrower's ability to repay; mortgage servicing rules; and prohibition on unfair, deceptive, or abusive acts (UDAAP).",
            "jurisdiction": "Federal (USA)",
            "citations": ["Dodd-Frank Act, Title X", "12 CFR Part 1026 (Regulation Z)", "ATR/QM Rule"],
            "keywords": ["cfpb", "ability to repay", "qualified mortgage", "udap", "udaap", "mortgage servicing"],
        },
    },
    "california": {
        "california_disclosure": {
            "title": "California Real Estate Disclosure Requirements",
            "body": "California has among the most extensive disclosure requirements in the US. Includes: Transfer Disclosure Statement (TDS), Natural Hazard Disclosure (NHD) — seismic, flood, fire, etc., Megan's Law disclosure, Mello-Roos (CFD) disclosure, lead-based paint (pre-1978), and property-specific disclosures (condominium CC&Rs, HOA docs, pest control reports). Seller must also disclose deaths on property within the last 3 years if asked.",
            "jurisdiction": "California",
            "citations": ["California Civil Code §§ 1102-1102.17", "Health & Safety Code § 25249.5 (Prop 65)"],
            "keywords": ["california", "tds", "nhd", "mello-roos", "natural hazard", "disclosure", "prop 65"],
        },
        "california_dre": {
            "title": "California Department of Real Estate (DRE) / Bureau of Real Estate",
            "body": "California DRE (now California Bureau of Real Estate — CalBRE) licenses and regulates real estate professionals. Requires: 3 college-level courses (Real Estate Principles, Practice, and one elective) for salesperson license; 8 courses for broker license; 45 hours of continuing education every 4 years; and mandatory trust fund handling.",
            "jurisdiction": "California",
            "citations": ["California Business and Professions Code §§ 10000-10580"],
            "keywords": ["california", "dre", "calbre", "licensing", "education", "broker", "salesperson"],
        },
        "prop13": {
            "title": "Proposition 13 — California Property Tax",
            "body": "Prop 13 (1978) limits property taxes to 1% of assessed value at time of purchase, with annual increases capped at 2% (or CPI, whichever is lower). Property reassessment occurs on transfer — but Prop 19 (2020) allows homeowners over 55, severely disabled, or wildfire victims to transfer their assessed value to a new home (within California).",
            "jurisdiction": "California",
            "citations": ["California Constitution Article XIIIA", "Prop 13 (1978)", "Prop 19 (2020)"],
            "keywords": ["prop 13", "california", "property tax", "assessment", "transfer", "prop 19"],
        },
    },
    "new_york": {
        "ny_disclosure": {
            "title": "New York Property Condition Disclosure Act",
            "body": "New York's Property Condition Disclosure Act requires sellers to complete a Property Condition Disclosure Statement (PCDS). However, the law allows sellers to opt out by paying a $500 credit to the buyer at closing. If the PCDS is provided, the seller faces liability for knowing omissions or misrepresentations.",
            "jurisdiction": "New York",
            "citations": ["NY Real Property Law § 462-475", "Property Condition Disclosure Act"],
            "keywords": ["new york", "pcds", "disclosure", "seller", "$500 credit"],
        },
        "ny_license": {
            "title": "New York Department of State (DOS) Licensing",
            "body": "New York's Division of Licensing Services licenses real estate professionals. Requires: 77-hour pre-licensure course for salesperson (longest in US); 152 hours for broker (including 1 year of experience); continuing education every 2 years; mandatory written exam. New York also requires brokerage trust accounts and strict record-keeping.",
            "jurisdiction": "New York",
            "citations": ["NY Real Property Law Article 12-A", "19 NYCRR Parts 175-195"],
            "keywords": ["new york", "dos", "licensing", "education", "salesperson", "broker", "trust account"],
        },
    },
    "texas": {
        "texas_trec": {
            "title": "Texas Real Estate Commission (TREC)",
            "body": "TREC licenses and regulates real estate professionals in Texas. IABS (Information About Brokerage Services) must be provided at first substantive contact. TREC promulgates standard contract forms (One to Four Family Residential Contract, etc.) — their use is mandatory for TREC-licensed agents. Requires 180 hours of education for salesperson license and 900 hours for broker.",
            "jurisdiction": "Texas",
            "citations": ["Texas Occupations Code Chapter 1101", "TREC Rules (22 TAC Chapter 535)"],
            "keywords": ["texas", "trec", "iabs", "contract forms", "licensing", "salesperson", "broker"],
        },
        "texas_disclosure": {
            "title": "Texas Seller Disclosure Notice",
            "body": "Texas requires a Seller's Disclosure Notice (TREC Form OP-H) covering condition of property items including structural, systems, environmental, and legal matters. Must be provided to buyer before signing the contract or within a specified timeframe. Property may be sold 'AS IS' with proper disclosure, but intentional concealment can result in liability.",
            "jurisdiction": "Texas",
            "citations": ["Texas Property Code § 5.008", "TREC Form OP-H"],
            "keywords": ["texas", "seller disclosure", "as is", "trec form", "property condition"],
        },
    },
    "florida": {
        "florida_frec": {
            "title": "Florida Real Estate Commission (FREC)",
            "body": "FREC regulates real estate under Chapter 475, Florida Statutes. Requires 63 hours of pre-licensure for salesperson, 72 hours for broker. Continuing education every 2 years (14 hours including 3 hours of law updates). Florida has strict rules on commission disputes, trust accounts, and advertising.",
            "jurisdiction": "Florida",
            "citations": ["Florida Statutes Chapter 475", "FREC Rules (61J2)"],
            "keywords": ["florida", "frec", "licensing", "education", "commission", "miami", "orlando"],
        },
        "florida_disclosure": {
            "title": "Florida Seller Disclosure",
            "body": "Florida does NOT have a statutory seller disclosure form required by law. Sellers are generally protected by caveat emptor (buyer beware) except for active concealment of known defects. However, the Florida Supreme Court recognized a cause of action for failure to disclose (Johnson v. Davis, 1985). A seller's real estate agent must disclose all known facts materially affecting the value of the property.",
            "jurisdiction": "Florida",
            "citations": ["Johnson v. Davis, 480 So. 2d 625 (Fla. 1985)", "Florida Statutes § 475"],
            "keywords": ["florida", "seller disclosure", "caveat emptor", "johnson v davis", "active concealment"],
        },
    },
    "general_usa": {
        "commission_rules": {
            "title": "Real Estate Commission & Antitrust (USA)",
            "body": "Following the Sitzer/Burnett and Nosalek class action lawsuits, the landscape of real estate commissions has changed significantly. Key changes: buyer broker commissions can no longer be set on MLS as a condition of listing; offers of compensation must be off-MLS or disclosed differently; buyers must sign written representation agreements. The NAR settlement (2024) requires MLS changes to remove compensation offers from MLS fields. Agents must clearly disclose their commission structure and obtain written agreements from buyers before showing properties.",
            "jurisdiction": "National (USA)",
            "citations": ["Sitzer/Burnett v. NAR (W.D. Mo. 2023)", "NAR Settlement Agreement 2024", "DOJ v. NAR"],
            "keywords": ["commission", "nar", "settlement", "sitzer", "buyer broker", "compensation", "antitrust"],
        },
        "licensing_reciprocity": {
            "title": "Real Estate Licensing Reciprocity (USA)",
            "body": "Most states have licensing reciprocity agreements, allowing licensed agents from one state to obtain a license in another state with reduced requirements. Generally: states within the same region (e.g., Western Regional Reciprocal) have agreements. However, states like California, New York, and Florida have limited or no reciprocity and require full pre-licensing. The ARELLO (Association of Real Estate License Law Officials) promotes national standards.",
            "jurisdiction": "Interstate (USA)",
            "citations": ["ARELLO Guidelines", "State-specific licensing statutes"],
            "keywords": ["reciprocity", "licensing", "interstate", "portability", "arello"],
        },
        "tax_implications": {
            "title": "Federal Tax Implications — Real Estate (USA)",
            "body": "Key federal tax provisions: Section 121 exclusion — up to $250k ($500k married) capital gains exclusion on primary residence (must own and live in for 2 of last 5 years); Section 1031 like-kind exchanges for investment property (deferred capital gains); mortgage interest deduction (limited to $750k acquisition debt after TCJA 2017); property tax deduction (limited to $10k SALT deduction).",
            "jurisdiction": "Federal (USA)",
            "citations": ["IRC § 121", "IRC § 1031", "Tax Cuts and Jobs Act 2017", "IRC § 163(h)"],
            "keywords": ["tax", "capital gains", "section 121", "section 1031", "mortgage interest", "salt"],
        },
        "environmental": {
            "title": "Environmental Regulations — Real Estate (USA)",
            "body": "Key environmental regulations: Lead-Based Paint Disclosure (Residential Lead-Based Paint Hazard Reduction Act of 1992) — required for all pre-1978 housing; CERCLA/Superfund liability for contaminated properties; wetlands regulations under Clean Water Act; asbestos in commercial properties; mold disclosure (state-specific); and radon testing disclosure (state-specific). Phase I ESA is standard for commercial transactions.",
            "jurisdiction": "Federal (USA), with state variations",
            "citations": ["Residential Lead-Based Paint Hazard Reduction Act, 42 USC § 4851", "CERCLA, 42 USC § 9601", "Clean Water Act § 404"],
            "keywords": ["lead paint", "environmental", "cercla", "superfund", "asbestos", "radon", "wetlands", "phase i"],
        },
    },
}


class RegulatoryService:
    """Queryable regulatory knowledge base for Canada and US real estate law."""

    def __init__(self):
        self._build_index()

    def _build_index(self):
        """Build a searchable keyword index from all regulations."""
        self._all_regs = []
        for country, country_key in [("Canada", CANADA_REGULATIONS), ("USA", USA_REGULATIONS)]:
            for jurisdiction, rules in country_key.items():
                for key, rule in rules.items():
                    rule["country"] = country
                    rule["jurisdiction_key"] = jurisdiction
                    rule["reg_key"] = key
                    self._all_regs.append(rule)

    def query(self, query_text: str, country: Optional[str] = None,
              jurisdiction: Optional[str] = None, limit: int = 5) -> list[dict]:
        """Search regulations by keyword matching. Returns ranked results."""
        if not query_text:
            return self._all_regs[:limit]

        query_lower = query_text.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        scored = []
        for reg in self._all_regs:
            if country and reg["country"].lower() != country.lower():
                continue
            if jurisdiction and jurisdiction.lower() not in reg["jurisdiction"].lower():
                continue

            text = (reg["title"] + " " + reg["body"] + " " +
                    " ".join(reg["keywords"])).lower()
            words = set(re.findall(r'\w+', text))

            exact_matches = sum(1 for qw in query_words if qw in words)
            partial_matches = sum(1 for qw in query_words if any(qw in w for w in words))

            # Bonus for keyword match
            kw = set(k.lower() for k in reg["keywords"])
            keyword_hits = sum(1 for qw in query_words if qw in kw)

            score = exact_matches * 3 + keyword_hits * 5 + partial_matches
            if score > 0:
                scored.append((score, reg))

        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]

    def get_by_jurisdiction(self, jurisdiction: str) -> list[dict]:
        """Get all regulations for a specific jurisdiction."""
        j_lower = jurisdiction.lower()
        return [
            r for r in self._all_regs
            if j_lower in r["jurisdiction"].lower() or j_lower in r["jurisdiction_key"].lower()
        ]

    def get_summary(self, country: Optional[str] = None) -> dict:
        """Get a summary of available regulatory topics."""
        regs = self._all_regs if not country else [
            r for r in self._all_regs if r["country"].lower() == country.lower()
        ]
        topics = {}
        for r in regs:
            j = r["jurisdiction"]
            if j not in topics:
                topics[j] = []
            topics[j].append(r["title"])
        return {
            "total_regulations": len(regs),
            "countries": list(set(r["country"] for r in regs)),
            "jurisdictions": list(topics.keys()),
            "topics": topics,
        }


# Singleton
_regulatory_service: Optional[RegulatoryService] = None


def get_regulatory_service() -> RegulatoryService:
    global _regulatory_service
    if _regulatory_service is None:
        _regulatory_service = RegulatoryService()
    return _regulatory_service
