# Finflate debranding gate

## Scope distinction

Historical internal sources may retain Finflate references as provenance.
Active product identity must not present Pepperyn as a Finflate product.

## Active repository removal surface found at handover preparation

- `frontend/app/contact/page.tsx`
- `frontend/components/ui/CreditsModal.tsx`
- `frontend/app/legal/rgpd/page.tsx`
- `frontend/app/app/billing/success/page.tsx`
- `frontend/app/legal/mentions-legales/page.tsx`
- `frontend/components/landing/FaqSection.tsx`
- `frontend/components/landing/Footer.tsx`
- `frontend/app/legal/donnees-securisees/page.tsx`
- `frontend/app/legal/confidentialite/page.tsx`
- `frontend/app/legal/cgu/page.tsx`
- `backend/routers/billing.py`
- `backend/services/export_pptx_service.py`
- tests that require `info@finflate.com` and must change with the active behavior.

The removal surface includes `Finflate SRL`, `info@finflate.com`,
`www.finflate.com`, “Powered by Finflate”, copyright, legal identity and support
instructions. Comments using Finflate only as a non-output example require
classification, not blind deletion.

## Replacement requirements

- Founder confirms the truthful legal/operator name and contact details.
- Active UI, authentication, onboarding, support, exports, emails, metadata,
  structured data, manifest/assets, legal pages and operational messages use the
  confirmed Pepperyn identity.
- No replacement legal entity is invented.
- Historical/internal sources remain intact when provenance is legitimate.
- Tests assert the new active identity and absence of active Finflate output.

## Deployed verification

Audit `www.pepperyn.com`, reachable routes, HTML/metadata, robots/indexable pages,
assets, forms, emails and generated exports after deployment. Repository cleanup
alone cannot pass the gate.

**Current status:** `OPEN — INVENTORY DEFINED; REPLACEMENT IDENTITY AND DEPLOYED
PROOF MISSING`.
