-- ==============================================================================
-- CAMPUS KONNECT - COMPLETE SUPABASE POSTGRESQL SCHEMA
-- Tagline: "One Campus. One Community. One Connected Platform."
-- ==============================================================================
-- This schema establishes tables, constraints, foreign keys, row level security
-- (RLS) policies, triggers, and storage buckets for the Campus Konnect MVP.
--
-- INSTRUCTIONS FOR SUPABASE:
-- 1. Open your Supabase Dashboard (https://supabase.com/dashboard)
-- 2. Select your project and navigate to the SQL Editor
-- 3. Paste and run this script completely.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXTENSIONS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 2. HELPER FUNCTIONS & TRIGGERS
-- ------------------------------------------------------------------------------
-- Function to automatically update 'updated_at' columns on record modification
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- 3. TABLE: PROFILES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    avatar_url TEXT DEFAULT '',
    department TEXT DEFAULT 'Computer Science',
    year INTEGER DEFAULT 1 CHECK (year >= 1 AND year <= 5),
    interests TEXT[] DEFAULT '{}'::TEXT[],
    bio TEXT DEFAULT '',
    role TEXT DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_department ON public.profiles(department);

-- Trigger for profiles updated_at
DROP TRIGGER IF EXISTS trigger_profiles_updated_at ON public.profiles;
CREATE TRIGGER trigger_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Function to check if the current requesting user has the admin role
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create a profile when a new user signs up via Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (
        id,
        email,
        full_name,
        department,
        year,
        interests,
        bio,
        role
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'department', 'Computer Science'),
        COALESCE((NEW.raw_user_meta_data->>'year')::INTEGER, 1),
        COALESCE(
            ARRAY(SELECT jsonb_array_elements_text(NEW.raw_user_meta_data->'interests')),
            '{}'::TEXT[]
        ),
        COALESCE(NEW.raw_user_meta_data->>'bio', ''),
        COALESCE(NEW.raw_user_meta_data->>'role', 'student')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ------------------------------------------------------------------------------
-- 4. TABLE: POSTS (Campus Feed)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'Announcement', 'Academic', 'Event', 'Opportunity', 'Club', 'Placement', 'General'
    )),
    image_url TEXT DEFAULT '',
    attachment_url TEXT DEFAULT '',
    is_pinned BOOLEAN DEFAULT FALSE,
    is_announcement BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_posts_author ON public.posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_category ON public.posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_pinned ON public.posts(is_pinned DESC, created_at DESC);

DROP TRIGGER IF EXISTS trigger_posts_updated_at ON public.posts;
CREATE TRIGGER trigger_posts_updated_at
    BEFORE UPDATE ON public.posts
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 5. TABLE: COMMENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON public.comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_author_id ON public.comments(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON public.comments(created_at ASC);

DROP TRIGGER IF EXISTS trigger_comments_updated_at ON public.comments;
CREATE TRIGGER trigger_comments_updated_at
    BEFORE UPDATE ON public.comments
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 6. TABLE: LIKES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_post_user_like UNIQUE (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_likes_post_id ON public.likes(post_id);
CREATE INDEX IF NOT EXISTS idx_likes_user_id ON public.likes(user_id);

-- ------------------------------------------------------------------------------
-- 7. TABLE: SAVED POSTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.saved_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_post_user_save UNIQUE (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_posts_user_id ON public.saved_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_posts_post_id ON public.saved_posts(post_id);

-- ------------------------------------------------------------------------------
-- 8. TABLE: EVENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'Workshop', 'Seminar', 'Hackathon', 'Club', 'Cultural', 'Sports', 'Placement', 'Academic', 'Other'
    )),
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    venue TEXT NOT NULL,
    organizer TEXT NOT NULL,
    registration_link TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    created_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_category ON public.events(category);
CREATE INDEX IF NOT EXISTS idx_events_created_by ON public.events(created_by);

DROP TRIGGER IF EXISTS trigger_events_updated_at ON public.events;
CREATE TRIGGER trigger_events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 9. TABLE: EVENT REGISTRATIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.event_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'registered' CHECK (status IN ('registered', 'cancelled')),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_event_user_reg UNIQUE (event_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_event_reg_event ON public.event_registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_event_reg_user ON public.event_registrations(user_id);

-- ------------------------------------------------------------------------------
-- 10. TABLE: RESOURCES (Academic Resource Hub)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    department TEXT NOT NULL,
    semester INTEGER DEFAULT 1 CHECK (semester >= 1 AND semester <= 10),
    subject TEXT NOT NULL,
    resource_type TEXT NOT NULL CHECK (resource_type IN (
        'Notes', 'Previous Year Paper', 'Lab Manual', 'Assignment', 'Presentation', 'Study Material', 'Reference', 'Other'
    )),
    file_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size_bytes BIGINT DEFAULT 0,
    uploaded_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resources_dept_sem ON public.resources(department, semester);
CREATE INDEX IF NOT EXISTS idx_resources_subject ON public.resources(subject);
CREATE INDEX IF NOT EXISTS idx_resources_type ON public.resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_uploaded_by ON public.resources(uploaded_by);

DROP TRIGGER IF EXISTS trigger_resources_updated_at ON public.resources;
CREATE TRIGGER trigger_resources_updated_at
    BEFORE UPDATE ON public.resources
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 11. TABLE: DISCUSSIONS (Student Forum)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.discussions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'Academics', 'Placements', 'Projects', 'Events', 'Clubs', 'General'
    )),
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_discussions_category ON public.discussions(category);
CREATE INDEX IF NOT EXISTS idx_discussions_author ON public.discussions(author_id);
CREATE INDEX IF NOT EXISTS idx_discussions_created_at ON public.discussions(created_at DESC);

DROP TRIGGER IF EXISTS trigger_discussions_updated_at ON public.discussions;
CREATE TRIGGER trigger_discussions_updated_at
    BEFORE UPDATE ON public.discussions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 12. TABLE: DISCUSSION COMMENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.discussion_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discussion_id UUID NOT NULL REFERENCES public.discussions(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_disc_comments_discussion ON public.discussion_comments(discussion_id);
CREATE INDEX IF NOT EXISTS idx_disc_comments_author ON public.discussion_comments(author_id);
CREATE INDEX IF NOT EXISTS idx_disc_comments_created_at ON public.discussion_comments(created_at ASC);

DROP TRIGGER IF EXISTS trigger_discussion_comments_updated_at ON public.discussion_comments;
CREATE TRIGGER trigger_discussion_comments_updated_at
    BEFORE UPDATE ON public.discussion_comments
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 13. ROW LEVEL SECURITY (RLS) POLICIES
-- ------------------------------------------------------------------------------

-- Enable RLS across all application tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discussions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discussion_comments ENABLE ROW LEVEL SECURITY;

-- 13.1 PROFILES POLICIES
DROP POLICY IF EXISTS "Public profiles are readable by authenticated users" ON public.profiles;
CREATE POLICY "Public profiles are readable by authenticated users"
    ON public.profiles FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile or admins update any" ON public.profiles;
CREATE POLICY "Users can update own profile or admins update any"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = id OR public.is_admin())
    WITH CHECK (auth.uid() = id OR public.is_admin());

-- 13.2 POSTS POLICIES
DROP POLICY IF EXISTS "Posts are readable by authenticated users" ON public.posts;
CREATE POLICY "Posts are readable by authenticated users"
    ON public.posts FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can create posts" ON public.posts;
CREATE POLICY "Authenticated users can create posts"
    ON public.posts FOR INSERT
    TO authenticated
    WITH CHECK (
        auth.uid() = author_id AND (
            (category != 'Announcement' AND is_announcement = FALSE AND is_pinned = FALSE)
            OR public.is_admin()
        )
    );

DROP POLICY IF EXISTS "Users can update own posts or admin" ON public.posts;
CREATE POLICY "Users can update own posts or admin"
    ON public.posts FOR UPDATE
    TO authenticated
    USING (auth.uid() = author_id OR public.is_admin())
    WITH CHECK (
        (auth.uid() = author_id AND category != 'Announcement' AND is_announcement = FALSE AND is_pinned = FALSE)
        OR public.is_admin()
    );

DROP POLICY IF EXISTS "Users can delete own posts or admin" ON public.posts;
CREATE POLICY "Users can delete own posts or admin"
    ON public.posts FOR DELETE
    TO authenticated
    USING (auth.uid() = author_id OR public.is_admin());

-- 13.3 COMMENTS POLICIES
DROP POLICY IF EXISTS "Comments are readable by authenticated users" ON public.comments;
CREATE POLICY "Comments are readable by authenticated users"
    ON public.comments FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can create comments" ON public.comments;
CREATE POLICY "Authenticated users can create comments"
    ON public.comments FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = author_id);

DROP POLICY IF EXISTS "Users can delete own comments or admin" ON public.comments;
CREATE POLICY "Users can delete own comments or admin"
    ON public.comments FOR DELETE
    TO authenticated
    USING (auth.uid() = author_id OR public.is_admin());

-- 13.4 LIKES POLICIES
DROP POLICY IF EXISTS "Likes are readable by authenticated users" ON public.likes;
CREATE POLICY "Likes are readable by authenticated users"
    ON public.likes FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can insert likes" ON public.likes;
CREATE POLICY "Authenticated users can insert likes"
    ON public.likes FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own likes" ON public.likes;
CREATE POLICY "Users can delete own likes"
    ON public.likes FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- 13.5 SAVED POSTS POLICIES
DROP POLICY IF EXISTS "Users can view their own saved posts" ON public.saved_posts;
CREATE POLICY "Users can view their own saved posts"
    ON public.saved_posts FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can save posts" ON public.saved_posts;
CREATE POLICY "Users can save posts"
    ON public.saved_posts FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can remove saved posts" ON public.saved_posts;
CREATE POLICY "Users can remove saved posts"
    ON public.saved_posts FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- 13.6 EVENTS POLICIES (Admins only for Create, Update, Delete)
DROP POLICY IF EXISTS "Events are readable by authenticated users" ON public.events;
CREATE POLICY "Events are readable by authenticated users"
    ON public.events FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Admins or creators can insert events" ON public.events;
DROP POLICY IF EXISTS "Only admins can insert events" ON public.events;
CREATE POLICY "Only admins can insert events"
    ON public.events FOR INSERT
    TO authenticated
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS "Admins or creators can update events" ON public.events;
DROP POLICY IF EXISTS "Only admins can update events" ON public.events;
CREATE POLICY "Only admins can update events"
    ON public.events FOR UPDATE
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS "Admins or creators can delete events" ON public.events;
DROP POLICY IF EXISTS "Only admins can delete events" ON public.events;
CREATE POLICY "Only admins can delete events"
    ON public.events FOR DELETE
    TO authenticated
    USING (public.is_admin());


-- 13.7 EVENT REGISTRATIONS POLICIES
DROP POLICY IF EXISTS "Users can view registrations" ON public.event_registrations;
CREATE POLICY "Users can view registrations"
    ON public.event_registrations FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id OR public.is_admin());

DROP POLICY IF EXISTS "Users can register for events" ON public.event_registrations;
CREATE POLICY "Users can register for events"
    ON public.event_registrations FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update or cancel own registration" ON public.event_registrations;
CREATE POLICY "Users can update or cancel own registration"
    ON public.event_registrations FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id OR public.is_admin())
    WITH CHECK (auth.uid() = user_id OR public.is_admin());

DROP POLICY IF EXISTS "Users can delete own registration" ON public.event_registrations;
CREATE POLICY "Users can delete own registration"
    ON public.event_registrations FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id OR public.is_admin());

-- 13.8 RESOURCES POLICIES
DROP POLICY IF EXISTS "Resources are readable by authenticated users" ON public.resources;
CREATE POLICY "Resources are readable by authenticated users"
    ON public.resources FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can upload resources" ON public.resources;
CREATE POLICY "Authenticated users can upload resources"
    ON public.resources FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = uploaded_by);

DROP POLICY IF EXISTS "Users can update own resources or admin" ON public.resources;
CREATE POLICY "Users can update own resources or admin"
    ON public.resources FOR UPDATE
    TO authenticated
    USING (auth.uid() = uploaded_by OR public.is_admin())
    WITH CHECK (auth.uid() = uploaded_by OR public.is_admin());

DROP POLICY IF EXISTS "Users can delete own resources or admin" ON public.resources;
CREATE POLICY "Users can delete own resources or admin"
    ON public.resources FOR DELETE
    TO authenticated
    USING (auth.uid() = uploaded_by OR public.is_admin());

-- 13.9 DISCUSSIONS POLICIES
DROP POLICY IF EXISTS "Discussions are readable by authenticated users" ON public.discussions;
CREATE POLICY "Discussions are readable by authenticated users"
    ON public.discussions FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can create discussions" ON public.discussions;
CREATE POLICY "Authenticated users can create discussions"
    ON public.discussions FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = author_id);

DROP POLICY IF EXISTS "Users can update own discussions or admin" ON public.discussions;
CREATE POLICY "Users can update own discussions or admin"
    ON public.discussions FOR UPDATE
    TO authenticated
    USING (auth.uid() = author_id OR public.is_admin())
    WITH CHECK (auth.uid() = author_id OR public.is_admin());

DROP POLICY IF EXISTS "Users can delete own discussions or admin" ON public.discussions;
CREATE POLICY "Users can delete own discussions or admin"
    ON public.discussions FOR DELETE
    TO authenticated
    USING (auth.uid() = author_id OR public.is_admin());

-- 13.10 DISCUSSION COMMENTS POLICIES
DROP POLICY IF EXISTS "Discussion comments are readable by authenticated users" ON public.discussion_comments;
CREATE POLICY "Discussion comments are readable by authenticated users"
    ON public.discussion_comments FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can comment on discussions" ON public.discussion_comments;
CREATE POLICY "Authenticated users can comment on discussions"
    ON public.discussion_comments FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = author_id);

DROP POLICY IF EXISTS "Users can delete own discussion comments or admin" ON public.discussion_comments;
CREATE POLICY "Users can delete own discussion comments or admin"
    ON public.discussion_comments FOR DELETE
    TO authenticated
    USING (auth.uid() = author_id OR public.is_admin());

-- ------------------------------------------------------------------------------
-- 14. STORAGE BUCKET CONFIGURATION & POLICIES
-- ------------------------------------------------------------------------------
-- Insert default storage buckets if not existing
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('profile-images', 'profile-images', true),
    ('resources', 'resources', true),
    ('post-media', 'post-media', true),
    ('event-images', 'event-images', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- Storage RLS: Public read for all authenticated users
DROP POLICY IF EXISTS "Allow authenticated read for profile images" ON storage.objects;
CREATE POLICY "Allow authenticated read for profile images"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (bucket_id IN ('profile-images', 'resources', 'post-media', 'event-images'));

-- Storage RLS: Allow authenticated uploads
DROP POLICY IF EXISTS "Allow authenticated uploads" ON storage.objects;
CREATE POLICY "Allow authenticated uploads"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id IN ('profile-images', 'resources', 'post-media', 'event-images'));

-- Storage RLS: Allow users to delete their own uploaded objects
DROP POLICY IF EXISTS "Allow owners to delete their uploads" ON storage.objects;
CREATE POLICY "Allow owners to delete their uploads"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (bucket_id IN ('profile-images', 'resources', 'post-media', 'event-images') AND (auth.uid()::text = (storage.foldername(name))[1] OR auth.uid() = owner));

-- ==============================================================================
-- 15. HOW TO ASSIGN AN ADMIN USER (FOR STUDENT DEMONSTRATION / VIVA)
-- ==============================================================================
-- Once a user has registered via the Campus Konnect interface, run this query:
--
-- UPDATE public.profiles
-- SET role = 'admin'
-- WHERE email = 'your-admin-email@college.edu';
-- ==============================================================================
