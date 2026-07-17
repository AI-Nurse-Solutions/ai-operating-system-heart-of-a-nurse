# Standalone Wellness Services Marketing & Management Lane

**Canonical lane:** `wellness_services_marketing_management`<br>
**Route:** `/wellness-services-marketing-managers`<br>
**Namespace:** `wellness_thrive.*`<br>
**Home:** `My THRIVE Mission Control`

This is a standalone population lane inside the Nurse AI OS ecosystem. It is not part of the nurse, student, educator, leader, practitioner, medical resident, respiratory therapy or hospital-administrator populations. It may share shell-level design tokens and a parent navigation card, but **no data, memory, schemas, permissions, connectors, source decisions, agent state or sensitive metrics cross lanes by default**.

## Partition contract

- All durable records begin with `wellness_thrive.` and include immutable `partition_id`, closed `acl`, source, owner, purpose, state, version and expiry.
- Parent Nurse AI OS may hold only a route label, icon, release version and coarse `not_installed|installing|ready|attention|paused` state after explicit approval.
- Parent Mission Control deep-links into THRIVE; it never renders campaign, audience, service, financial, personal or agent details.
- Cross-lane export is Off. A later export requires a new human-approved feature, minimum-necessary field map, destination ACL, expiry and tamper-evident receipt.
- Reinstall resumes or repairs the canonical instance. It never forks a second source of truth or silently migrates schemas.

## Base-product data ceiling

Even in an approved institution workspace, THRIVE accepts only approved aggregate, public, synthetic or process-level inputs. It does not accept row-level data labeled deidentified and does not perform in-model deidentification. It rejects PHI; patient/client records; raw feedback/comments; individual consumer-sensitive data; individual workforce data; device/household identifiers; individual lead, contact, prospect, attendee, referral, booking, scheduling, purchase, billing, testimonial-subject or influencer records.
