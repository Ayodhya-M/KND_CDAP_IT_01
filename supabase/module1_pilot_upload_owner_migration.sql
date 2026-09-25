-- Module 1 pilot upload support.
-- The current pilot frontend has no login/session, so uploaded_by must be
-- optional until authenticated uploads are introduced.

ALTER TABLE public.dataset_uploads
    ALTER COLUMN uploaded_by DROP NOT NULL;
