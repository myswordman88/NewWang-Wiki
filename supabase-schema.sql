-- =========================================================
-- 新王觉醒 · BD 数据表 + 行级安全策略 (RLS)
-- 用途：在 Supabase 控制台的 SQL Editor 中全选执行本文件
-- 权限模型：
--   公开可读已发布的 BD；登录用户可读/写/删自己的 BD
--   anon key 前端公开，安全完全由下方 RLS 策略保证
-- =========================================================

create table if not exists public.bds (
  id          uuid        primary key default gen_random_uuid(),
  user_id     uuid        not null references auth.users(id) on delete cascade,
  title       text        not null default '未命名 BD',
  class       text,
  data        jsonb       not null default '{}'::jsonb,
  is_public   boolean     not null default false,
  author_name text,
  likes       integer     not null default 0,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index if not exists bds_user_idx     on public.bds(user_id);
create index if not exists bds_public_idx   on public.bds(is_public, created_at desc);

alter table public.bds enable row level security;

-- 公开可读：任何人都能看 is_public = true 的 BD
drop policy if exists "bds_select_public" on public.bds;
create policy "bds_select_public" on public.bds
  for select using ( is_public = true );

-- 登录用户可读自己的全部 BD（含未发布草稿）
drop policy if exists "bds_select_own" on public.bds;
create policy "bds_select_own" on public.bds
  for select using ( auth.uid() = user_id );

-- 仅本人可插入（必须写入自己的 user_id，with check 校验）
drop policy if exists "bds_insert_own" on public.bds;
create policy "bds_insert_own" on public.bds
  for insert with check ( auth.uid() = user_id );

-- 仅本人可更新
drop policy if exists "bds_update_own" on public.bds;
create policy "bds_update_own" on public.bds
  for update using ( auth.uid() = user_id ) with check ( auth.uid() = user_id );

-- 仅本人可删除
drop policy if exists "bds_delete_own" on public.bds;
create policy "bds_delete_own" on public.bds
  for delete using ( auth.uid() = user_id );

-- updated_at 自动维护
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end; $$;

drop trigger if exists bds_set_updated_at on public.bds;
create trigger bds_set_updated_at before update on public.bds
  for each row execute function public.set_updated_at();
