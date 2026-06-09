-- ============================================================
-- SISTEM MULTI-ROLE USER — API Gateway UMKM (Kelompok 7)
-- Database : TugasGateaway
-- Roles    : admin | operator | end_user
-- ============================================================

USE `TugasGateaway`;

-- ============================================================
-- 1. TABEL: roles
--    Menyimpan definisi role yang tersedia
-- ============================================================
CREATE TABLE IF NOT EXISTS `roles` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `nama_role`   VARCHAR(50)  NOT NULL COMMENT 'admin | operator | end_user',
  `deskripsi`   TEXT,
  `created_at`  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_nama_role` (`nama_role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Definisi role / jabatan pengguna';

-- Seed: isi 3 role default
INSERT INTO `roles` (`nama_role`, `deskripsi`) VALUES
  ('admin',    'Administrator sistem — kontrol penuh atas seluruh konfigurasi, user, apps, dan data'),
  ('operator', 'Operator tagihan — kelola tagihan, monitoring transaksi, dan generate laporan'),
  ('end_user', 'Pengguna akhir — hanya dapat melihat data milik sendiri dan melakukan request transaksi');


-- ============================================================
-- 2. TABEL: permissions
--    Katalog semua hak akses / permission yang ada
-- ============================================================
CREATE TABLE IF NOT EXISTS `permissions` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `kode`        VARCHAR(80)  NOT NULL COMMENT 'Kode unik permission, misal: user.create',
  `grup`        VARCHAR(50)  NOT NULL COMMENT 'Grup: user | app | transaksi | monitor | billing | system',
  `deskripsi`   VARCHAR(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_kode` (`kode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Katalog seluruh hak akses dalam sistem';

-- Seed: daftar permission per grup
INSERT INTO `permissions` (`kode`, `grup`, `deskripsi`) VALUES
  -- === USER MANAGEMENT ===
  ('user.view_all',       'user',       'Lihat daftar semua user'),
  ('user.create',         'user',       'Tambah user baru'),
  ('user.edit',           'user',       'Edit data user (role, status, dll)'),
  ('user.delete',         'user',       'Hapus user dari sistem'),
  ('user.reset_password', 'user',       'Reset password user lain'),
  ('user.view_self',      'user',       'Lihat data profil sendiri'),
  ('user.edit_self',      'user',       'Edit profil sendiri (nama, password)'),

  -- === APP MANAGEMENT ===
  ('app.register',        'app',        'Daftarkan aplikasi baru ke Gateway'),
  ('app.view_all',        'app',        'Lihat semua aplikasi terdaftar'),
  ('app.view_self',       'app',        'Lihat detail aplikasi milik sendiri'),
  ('app.upgrade_paket',   'app',        'Upgrade paket langganan aplikasi'),
  ('app.delete',          'app',        'Hapus / nonaktifkan aplikasi'),
  ('app.manage_pricing',  'app',        'Kelola paket pricing (tambah/edit/hapus paket)'),

  -- === ROUTING & TRANSAKSI ===
  ('routing.send',        'transaksi',  'Kirim request routing ke aplikasi lain via Gateway'),
  ('routing.backtrack',   'transaksi',  'Gunakan endpoint backtracking routing'),
  ('routing.view_table',  'transaksi',  'Lihat routing table & route candidates'),
  ('transaksi.view_own',  'transaksi',  'Lihat riwayat transaksi milik sendiri'),
  ('transaksi.view_all',  'transaksi',  'Lihat semua riwayat transaksi seluruh user'),

  -- === BILLING & TAGIHAN ===
  ('billing.view_own',    'billing',    'Lihat tagihan & fee milik sendiri / aplikasi sendiri'),
  ('billing.view_all',    'billing',    'Lihat tagihan semua aplikasi / user'),
  ('billing.generate',    'billing',    'Generate laporan tagihan (PDF/export)'),
  ('billing.adjust',      'billing',    'Koreksi / sesuaikan tagihan secara manual'),

  -- === MONITORING ===
  ('monitor.view',        'monitor',    'Akses halaman monitor (request stats, health)'),
  ('monitor.health_log',  'monitor',    'Lihat health log semua service'),
  ('monitor.backtrack_stats','monitor', 'Lihat statistik backtracking routing'),

  -- === LOGGING ===
  ('log.view_all',        'system',     'Lihat semua log request dari seluruh user'),
  ('log.view_own',        'system',     'Lihat log request milik sendiri saja'),
  ('log.delete',          'system',     'Hapus log lama / arsip log'),

  -- === SYSTEM / ADMIN ===
  ('system.config',       'system',     'Ubah konfigurasi sistem (rate limit, fee default, dll)'),
  ('system.token_gen',    'system',     'Generate token JWT untuk testing'),
  ('system.audit',        'system',     'Lihat audit trail perubahan data sistem');


-- ============================================================
-- 3. TABEL: role_permissions
--    Mapping: role → daftar permission yang dimiliki
-- ============================================================
CREATE TABLE IF NOT EXISTS `role_permissions` (
  `role_id`       INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`),
  CONSTRAINT `fk_rp_role`       FOREIGN KEY (`role_id`)       REFERENCES `roles`(`id`)       ON DELETE CASCADE,
  CONSTRAINT `fk_rp_permission` FOREIGN KEY (`permission_id`) REFERENCES `permissions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Hak akses per role (many-to-many)';

-- Seed: mapping role → permissions
-- ADMIN (id=1) — semua permission
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
  SELECT 1, id FROM `permissions`;

-- OPERATOR (id=2) — billing, monitor, log terbatas, transaksi view
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
  SELECT 2, id FROM `permissions`
  WHERE `kode` IN (
    'user.view_self',
    'user.edit_self',
    'app.view_all',
    'app.view_self',
    'routing.view_table',
    'transaksi.view_all',
    'billing.view_all',
    'billing.generate',
    'billing.adjust',
    'monitor.view',
    'monitor.health_log',
    'monitor.backtrack_stats',
    'log.view_all',
    'system.token_gen'
  );

-- END USER (id=3) — akses minimal hanya untuk diri sendiri
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
  SELECT 3, id FROM `permissions`
  WHERE `kode` IN (
    'user.view_self',
    'user.edit_self',
    'app.register',
    'app.view_self',
    'app.upgrade_paket',
    'routing.send',
    'routing.backtrack',
    'routing.view_table',
    'transaksi.view_own',
    'billing.view_own',
    'log.view_own',
    'system.token_gen'
  );


-- ============================================================
-- 4. TABEL: users
--    Data pengguna sistem dengan role dan status
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id`            INT           NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(80)   NOT NULL,
  `email`         VARCHAR(150)  NOT NULL,
  `password_hash` VARCHAR(255)  NOT NULL COMMENT 'bcrypt hash password',
  `full_name`     VARCHAR(150)  DEFAULT NULL,
  `role_id`       INT           NOT NULL DEFAULT 3 COMMENT 'FK ke tabel roles',
  `status`        ENUM('aktif','nonaktif','banned') NOT NULL DEFAULT 'aktif',
  `api_key_ref`   VARCHAR(64)   DEFAULT NULL COMMENT 'Referensi api_key di registered_apps (jika end_user punya app)',
  `last_login`    DATETIME      DEFAULT NULL,
  `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_username` (`username`),
  UNIQUE KEY `uq_email`    (`email`),
  CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Tabel pengguna sistem API Gateway';

-- Seed: 1 user per role (password default = "password123" → bcrypt hash)
INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `status`) VALUES
  ('admin_gateway',
   'admin@gateway.umkm',
   '$2b$12$KixMrfEIy9ZEqlB7oLKVxeO/8SmZ2g4q0k.HY9NvP2Oq/kpYJFzyi',
   'Administrator Utama',
   1,
   'aktif'),
  ('operator_01',
   'operator@gateway.umkm',
   '$2b$12$KixMrfEIy9ZEqlB7oLKVxeO/8SmZ2g4q0k.HY9NvP2Oq/kpYJFzyi',
   'Operator Tagihan',
   2,
   'aktif'),
  ('enduser_demo',
   'enduser@gateway.umkm',
   '$2b$12$KixMrfEIy9ZEqlB7oLKVxeO/8SmZ2g4q0k.HY9NvP2Oq/kpYJFzyi',
   'Demo End User',
   3,
   'aktif');


-- ============================================================
-- 5. TABEL: user_sessions
--    Riwayat login & sesi JWT aktif per user
-- ============================================================
CREATE TABLE IF NOT EXISTS `user_sessions` (
  `id`          INT           NOT NULL AUTO_INCREMENT,
  `user_id`     INT           NOT NULL,
  `token_hash`  VARCHAR(255)  NOT NULL COMMENT 'Hash dari JWT session token',
  `ip_address`  VARCHAR(45)   DEFAULT NULL,
  `user_agent`  VARCHAR(255)  DEFAULT NULL,
  `login_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
  `expires_at`  DATETIME      NOT NULL,
  `is_active`   TINYINT(1)    NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_user_id`    (`user_id`),
  KEY `idx_token_hash` (`token_hash`(32)),
  CONSTRAINT `fk_sessions_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Sesi login aktif pengguna';


-- ============================================================
-- 6. TABEL: user_activity_log
--    Audit trail — setiap aksi penting dicatat
-- ============================================================
CREATE TABLE IF NOT EXISTS `user_activity_log` (
  `id`          INT           NOT NULL AUTO_INCREMENT,
  `user_id`     INT           DEFAULT NULL,
  `username`    VARCHAR(80)   DEFAULT NULL COMMENT 'Snapshot username saat aksi',
  `aksi`        VARCHAR(100)  NOT NULL COMMENT 'login | logout | create_user | delete_app | dll',
  `target`      VARCHAR(150)  DEFAULT NULL COMMENT 'Objek yang dikenai aksi',
  `detail`      JSON          DEFAULT NULL COMMENT 'Detail tambahan aksi',
  `ip_address`  VARCHAR(45)   DEFAULT NULL,
  `created_at`  DATETIME      DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id`   (`user_id`),
  KEY `idx_aksi`      (`aksi`),
  KEY `idx_created`   (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Audit trail aktivitas pengguna';


-- ============================================================
-- VIEW: v_user_permissions
--    Helper view untuk cek permission lengkap per user
-- ============================================================
CREATE OR REPLACE VIEW `v_user_permissions` AS
  SELECT
    u.id          AS user_id,
    u.username,
    u.email,
    r.nama_role,
    r.deskripsi   AS deskripsi_role,
    p.kode        AS permission,
    p.grup,
    p.deskripsi   AS deskripsi_permission,
    u.status      AS status_user
  FROM `users` u
  JOIN `roles`            r  ON u.role_id       = r.id
  JOIN `role_permissions` rp ON rp.role_id      = r.id
  JOIN `permissions`      p  ON rp.permission_id = p.id
  ORDER BY u.username, p.grup, p.kode;


-- ============================================================
-- VIEW: v_role_summary
--    Ringkasan jumlah permission per role
-- ============================================================
CREATE OR REPLACE VIEW `v_role_summary` AS
  SELECT
    r.id,
    r.nama_role,
    r.deskripsi,
    COUNT(rp.permission_id) AS total_permissions,
    GROUP_CONCAT(p.kode ORDER BY p.kode SEPARATOR ' | ') AS daftar_permission
  FROM `roles` r
  LEFT JOIN `role_permissions` rp ON rp.role_id = r.id
  LEFT JOIN `permissions`      p  ON p.id = rp.permission_id
  GROUP BY r.id, r.nama_role, r.deskripsi;


-- ============================================================
-- VERIFIKASI — jalankan untuk cek hasil
-- ============================================================
-- SELECT * FROM v_role_summary;
-- SELECT * FROM v_user_permissions WHERE username = 'admin_gateway';
-- SELECT * FROM v_user_permissions WHERE username = 'operator_01';
-- SELECT * FROM v_user_permissions WHERE username = 'enduser_demo';
