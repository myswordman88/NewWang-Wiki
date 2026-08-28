/* =========================================================
   新王觉醒 · Supabase 配置（部署前必填）
   ---------------------------------------------------------
   1. 到 https://supabase.com 新建项目
   2. 左侧 Project Settings → API
   3. 复制 Project URL 与 anon public key，替换下面占位
   说明：anon key 本就是设计给前端公开使用的（权限由数据库
        RLS 策略保证），因此放前端是安全的，无需隐藏。
   ========================================================= */
window.APP_CONFIG = {
  SUPABASE_URL: 'https://dnqmxuxwkliywtbxlwik.supabase.co',
  SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRucW14dXh3a2xpeXd0Ynhsd2lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY5Nzk4NzIsImV4cCI6MjEwMjU1NTg3Mn0.B3sE4WTkrFTDPutoJNtzHkwmFrqSCe2Z6ymwfg9CDRc'
};
