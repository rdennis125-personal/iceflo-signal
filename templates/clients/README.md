# Client Template Packs

Client-specific Jinja email templates live here when branding, layout, or report presentation should be kept separate from generic ICEFLO Signal templates.

Templates should receive already-curated values from transformation outputs. Keep metric calculations and recipient selection in Python/config layers rather than in the HTML templates.

Template packs should be registered by stable template IDs, then rendered through `EmailTemplateFactory` with a shared `EmailEnvelope` and a template-specific payload model.
