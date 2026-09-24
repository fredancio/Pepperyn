# Finflate debranding gate

## Scope distinction

Historical internal sources may retain Finflate references as provenance.
Active product identity must not present Pepperyn as a Finflate product.

2026-09-24 Founder decision: public brand **Insight Shaper**, same product;
operator **Frédéric Anciaux — individual/in his own name**; target
`insightshaper.com`. Internal Pepperyn/Finflate provenance is preserved. No global
replacement or technical identifier rename. Founder-reported old-domain 404 does
not satisfy repository, alternate-deployment or future deployed debranding proof.

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

- Operator name/status confirmed as above; publication/contact details remain
  to be supplied when necessary. Invent no address, company or support mailbox.
- Active UI, authentication, onboarding, support, exports, emails, metadata,
  structured data, manifest/assets, legal pages and operational messages use the
  confirmed Insight Shaper public identity.
- No replacement legal entity is invented.
- Historical/internal sources remain intact when provenance is legitimate.
- Tests assert the new active identity and absence of active Finflate output.

## Deployed verification

Audit the authorized `insightshaper.com` deployment, reachable routes, HTML/metadata, robots/indexable pages,
assets, forms, emails and generated exports after deployment. Repository cleanup
alone cannot pass the gate.

**Current status:** `OPEN — BRAND AND OPERATOR DECIDED; IMPLEMENTATION, PUBLICATION
DETAILS AND DEPLOYED PROOF MISSING`.

Minimum before Beta: coherent name on login/app, basic wordmark/title/favicon,
active metadata, visible export branding (not historical source filenames/IDs),
enabled invitation/recovery emails, operator/legal/support surfaces and links.
Unused commercial routes must be inaccessible rather than cosmetically rebuilt.
Keep private canonical identifiers and historical wording intact; label provenance
where exposed instead of falsifying old evidence. No production deployment here.
Defer custom logo/art direction, marketing landing expansion, SEO campaigns,
full historical user-document redesign and internal renaming. B8 is an identity
and truthful-publication gate, not a brand-design programme.
