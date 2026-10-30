-- ゲストからGoogleアカウントなどに切り替えたとき、public.users を合わせる。
-- 0001 の on_auth_user_created は「作るとき」だけなので、切り替えた後も
-- is_anonymous が true、mail が null のまま残ってしまうため。

create or replace function public.handle_auth_user_updated()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  update public.users
  set mail = new.email,
      is_anonymous = coalesce(new.is_anonymous, false)
  where id = new.id;
  return new;
end;
$$;

-- メールアドレスかゲストの印が変わったときだけ動かす
create trigger on_auth_user_updated
  after update of email, is_anonymous on auth.users
  for each row
  when (
    old.email is distinct from new.email
    or old.is_anonymous is distinct from new.is_anonymous
  )
  execute function public.handle_auth_user_updated();
