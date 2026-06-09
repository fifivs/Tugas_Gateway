-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jun 08, 2026 at 01:01 PM
-- Server version: 8.0.30
-- PHP Version: 8.4.11

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `tugasgateway`
--

-- --------------------------------------------------------

--
-- Table structure for table `api_health_log`
--

CREATE TABLE `api_health_log` (
  `id` int NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  `app_name` varchar(100) DEFAULT NULL,
  `endpoint` varchar(200) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `response_time_ms` int DEFAULT NULL,
  `status_code` int DEFAULT NULL,
  `error_message` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `api_health_log`
--

INSERT INTO `api_health_log` (`id`, `timestamp`, `app_name`, `endpoint`, `status`, `response_time_ms`, `status_code`, `error_message`) VALUES
(1, '2026-06-02 03:31:24', 'MyApp', '/health', 'online', 120, 200, NULL),
(2, '2026-06-02 15:17:39', 'SmartBank', '/smartbank/manajemen_saldo', 'online', 23, 404, NULL),
(3, '2026-06-02 15:17:39', 'SmartBank', '/smartbank/pembayaran_transaksi', 'online', 163, 404, NULL),
(4, '2026-06-02 15:17:44', 'Marketplace', '/marketplace/browse_produk', 'offline', 2116, NULL, 'Failed to fetch'),
(5, '2026-06-02 15:17:45', 'Marketplace', '/marketplace/checkout', 'offline', 262, NULL, 'Failed to fetch'),
(6, '2026-06-02 15:17:50', 'API Gateway', '/generate_token_tester/test_user', 'online', 124, 200, NULL),
(7, '2026-06-02 15:17:50', 'API Gateway', '/integrator/validasi_request', 'online', 22, 200, NULL),
(8, '2026-06-02 15:17:50', 'API Gateway', '/integrator/biaya_layanan_integrasi', 'online', 24, 200, NULL),
(9, '2026-06-02 15:17:50', 'SmartBank', '/smartbank/pembayaran_transaksi', 'online', 39, 404, NULL),
(10, '2026-06-02 15:17:50', 'SmartBank', '/smartbank/manajemen_saldo', 'online', 20, 404, NULL),
(11, '2026-06-02 15:17:52', 'Marketplace', '/marketplace/browse_produk', 'offline', 2046, NULL, 'Failed to fetch'),
(12, '2026-06-02 15:17:53', 'Marketplace', '/marketplace/checkout', 'offline', 260, NULL, 'Failed to fetch'),
(13, '2026-06-02 15:17:55', 'POS (WarungPOS)', '/pos/input_transaksi', 'offline', 2037, NULL, 'Failed to fetch'),
(14, '2026-06-02 15:17:55', 'POS (WarungPOS)', '/pos/pembayaran', 'offline', 265, NULL, 'Failed to fetch'),
(15, '2026-06-02 15:17:57', 'SupplierHub', '/supplierhub/order_bahan', 'offline', 2071, NULL, 'Failed to fetch'),
(16, '2026-06-02 15:17:57', 'SupplierHub', '/supplierhub/konfirmasi_stok', 'offline', 258, NULL, 'Failed to fetch'),
(17, '2026-06-02 15:17:59', 'LogistiKita', '/logistikita/request_pengiriman', 'offline', 2069, NULL, 'Failed to fetch'),
(18, '2026-06-02 15:18:00', 'LogistiKita', '/logistikita/tracking_status', 'offline', 258, NULL, 'Failed to fetch');

-- --------------------------------------------------------

--
-- Table structure for table `api_request_log`
--

CREATE TABLE `api_request_log` (
  `id` int NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  `user_id` varchar(100) DEFAULT NULL,
  `source_app` varchar(100) DEFAULT NULL,
  `endpoint` varchar(200) DEFAULT NULL,
  `amount` decimal(15,2) DEFAULT NULL,
  `fee` decimal(15,2) DEFAULT NULL,
  `jwt_valid` tinyint(1) DEFAULT NULL,
  `smartbank_status` varchar(50) DEFAULT NULL,
  `response_time_ms` int DEFAULT NULL,
  `status_gateway` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `api_request_log`
--

INSERT INTO `api_request_log` (`id`, `timestamp`, `user_id`, `source_app`, `endpoint`, `amount`, `fee`, `jwt_valid`, `smartbank_status`, `response_time_ms`, `status_gateway`) VALUES
(1, '2026-06-02 03:38:29', 'web', 'satelit', '/integrator/routing_api', '10000.00', '50.00', 1, 'gagal', 2476, 'FAILED'),
(2, '2026-06-02 15:03:41', 'user123', 'pos', '/integrator/routing_universal → marketplace', '50000.00', '250.00', 1, 'gagal', 3041, 'FAILED');

-- --------------------------------------------------------

--
-- Table structure for table `backtracking_log`
--

CREATE TABLE `backtracking_log` (
  `id` int NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  `user_id` varchar(100) DEFAULT NULL,
  `target_app` varchar(100) DEFAULT NULL,
  `total_candidates` int DEFAULT NULL,
  `total_attempts` int DEFAULT NULL,
  `route_used` varchar(50) DEFAULT NULL,
  `final_status` varchar(20) DEFAULT NULL,
  `trace` json DEFAULT NULL,
  `response_time_ms` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `backtracking_log`
--

INSERT INTO `backtracking_log` (`id`, `timestamp`, `user_id`, `target_app`, `total_candidates`, `total_attempts`, `route_used`, `final_status`, `trace`, `response_time_ms`) VALUES
(1, '2026-06-07 15:45:05', 'user_backtrack_test', 'smartbank', 3, 3, 'none', 'gagal', '[{\"url\": \"http://127.0.0.1:8000/smartbank/pembayaran_transaksi\", \"aksi\": \"BACKTRACK → coba kandidat #2 (mirror)\", \"step\": 1, \"error\": \"ConnectError\", \"label\": \"primary\", \"status\": \"GAGAL_BACKTRACK\", \"priority\": 1, \"error_detail\": \"Tidak bisa konek ke http://127.0.0.1:8000/smartbank/pembayaran_transaksi\"}, {\"url\": \"http://127.0.0.1:9000/smartbank/pembayaran_transaksi\", \"aksi\": \"BACKTRACK → coba kandidat #3 (fallback)\", \"step\": 2, \"error\": \"ConnectError\", \"label\": \"mirror\", \"status\": \"GAGAL_BACKTRACK\", \"priority\": 2, \"error_detail\": \"Tidak bisa konek ke http://127.0.0.1:9000/smartbank/pembayaran_transaksi\"}, {\"url\": \"http://127.0.0.1:8000/smartbank/health\", \"aksi\": \"Semua kandidat habis — tidak ada lagi yang bisa dicoba\", \"step\": 3, \"error\": \"ConnectError\", \"label\": \"fallback\", \"status\": \"GAGAL_BACKTRACK\", \"priority\": 3, \"error_detail\": \"Tidak bisa konek ke http://127.0.0.1:8000/smartbank/health\"}]', 7045);

-- --------------------------------------------------------

--
-- Table structure for table `logs_transaksi`
--

CREATE TABLE `logs_transaksi` (
  `id` int NOT NULL,
  `user_id` varchar(100) DEFAULT NULL,
  `endpoint` varchar(200) DEFAULT NULL,
  `waktu` datetime DEFAULT NULL,
  `detail` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `logs_transaksi`
--

INSERT INTO `logs_transaksi` (`id`, `user_id`, `endpoint`, `waktu`, `detail`) VALUES
(1, 'web', '/integrator/routing_api', '2026-06-02 02:55:25', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWxmYSIsImV4cCI6MTc4MDM0NTUxNH0.mkdhv7QrMVVGFrbl0Tp4z1y3ebPC7mtyQKAHW1W3Wwk\", \"amount\": 10000, \"api_key\": \"mya_02d8c78c70038039ec8369e72bbf759a\", \"source_app\": \"MyApp\"}'),
(2, 'web', '/integrator/routing_api', '2026-06-02 03:38:27', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWxmYSIsImV4cCI6MTc4MDM0ODA3OX0.k6d3JjbW30bZ1FIXzSM-w752DHon6oNCGVBC9Yqk8b0\", \"amount\": 10000, \"api_key\": \"sat_c4f38c1fd9c81efba3f13095a636b8a6\", \"source_app\": \"satelit\"}'),
(3, 'user123', '/integrator/routing_api', '2026-06-02 15:02:20', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(4, 'user123', '/integrator/routing_universal → marketplace', '2026-06-02 15:03:38', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": 50000, \"source_app\": \"pos\", \"target_app\": \"marketplace\"}'),
(5, 'user123', '/integrator/routing_api', '2026-06-02 15:08:12', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(6, 'user123', '/integrator/routing_api', '2026-06-02 15:08:12', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(7, 'user123', '/integrator/routing_api', '2026-06-02 15:08:13', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(8, 'user123', '/integrator/routing_api', '2026-06-02 15:08:13', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(9, 'user123', '/integrator/routing_api', '2026-06-02 15:08:14', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(10, 'user123', '/integrator/routing_api', '2026-06-02 15:08:14', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(11, 'user123', '/integrator/routing_api', '2026-06-02 15:08:15', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEyMyIsImV4cCI6MTc4MDM4OTA3MX0.tOAPowHhe_aG5Fe6dEbaO8D429aOdXg972jvIKIxW1s\", \"amount\": -500}'),
(12, 'user_backtrack_test', '/integrator/routing_backtracking → smartbank', '2026-06-07 15:44:58', '{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl9iYWNrdHJhY2tfdGVzdCIsImV4cCI6MTc4MDgyMzY5MH0.qLmkweq7B3bJvnVYGoF-oVEJC1b7A5az4lXxVFBoQiM\", \"amount\": 50000, \"source_app\": \"backtracking_tester\", \"target_app\": \"smartbank\"}');

-- --------------------------------------------------------

--
-- Table structure for table `pricing_plans`
--

CREATE TABLE `pricing_plans` (
  `id` int NOT NULL,
  `nama_paket` varchar(50) NOT NULL,
  `harga_per_bulan` decimal(12,2) NOT NULL DEFAULT '0.00',
  `quota_per_bulan` int NOT NULL DEFAULT '500',
  `fee_transaksi_persen` decimal(5,3) NOT NULL DEFAULT '0.500',
  `akses_routing` tinyint(1) NOT NULL DEFAULT '0',
  `akses_validasi` tinyint(1) NOT NULL DEFAULT '1',
  `akses_logging` tinyint(1) NOT NULL DEFAULT '1',
  `akses_biaya` tinyint(1) NOT NULL DEFAULT '1',
  `akses_monitor` tinyint(1) NOT NULL DEFAULT '0',
  `deskripsi` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `pricing_plans`
--

INSERT INTO `pricing_plans` (`id`, `nama_paket`, `harga_per_bulan`, `quota_per_bulan`, `fee_transaksi_persen`, `akses_routing`, `akses_validasi`, `akses_logging`, `akses_biaya`, `akses_monitor`, `deskripsi`, `created_at`) VALUES
(1, 'Starter', '0.00', 500, '0.500', 0, 1, 1, 1, 0, 'Paket gratis untuk coba-coba. Akses endpoint validasi & logging saja.', '2026-06-02 02:31:25'),
(2, 'Basic', '50000.00', 5000, '0.500', 1, 1, 1, 1, 0, 'Paket harian untuk UMKM kecil. Sudah bisa routing transaksi ke SmartBank.', '2026-06-02 02:31:25'),
(3, 'Pro', '200000.00', 50000, '0.400', 1, 1, 1, 1, 1, 'Paket profesional. Fee lebih hemat & akses monitor penuh.', '2026-06-02 02:31:25'),
(4, 'Enterprise', '500000.00', -1, '0.300', 1, 1, 1, 1, 1, 'Kuota unlimited. Fee terendah. Cocok untuk platform besar.', '2026-06-02 02:31:25');

-- --------------------------------------------------------

--
-- Table structure for table `registered_apps`
--

CREATE TABLE `registered_apps` (
  `id` int NOT NULL,
  `app_name` varchar(100) NOT NULL,
  `api_key` varchar(64) NOT NULL,
  `nama_paket` varchar(50) NOT NULL DEFAULT 'Starter',
  `quota_sisa` int NOT NULL DEFAULT '500',
  `quota_reset_date` date DEFAULT NULL,
  `aktif_sampai` date DEFAULT NULL,
  `total_request` int NOT NULL DEFAULT '0',
  `total_fee_dibayar` decimal(15,2) NOT NULL DEFAULT '0.00',
  `status` varchar(20) NOT NULL DEFAULT 'aktif',
  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `registered_apps`
--

INSERT INTO `registered_apps` (`id`, `app_name`, `api_key`, `nama_paket`, `quota_sisa`, `quota_reset_date`, `aktif_sampai`, `total_request`, `total_fee_dibayar`, `status`, `registered_at`) VALUES
(1, 'MyApp', 'mya_02d8c78c70038039ec8369e72bbf759a', 'Starter', 500, '2026-07-02', '2026-07-02', 0, '0.00', 'aktif', '2026-06-02 02:48:42'),
(2, 'satelit', 'sat_c4f38c1fd9c81efba3f13095a636b8a6', 'Basic', 5000, '2026-07-02', '2026-07-02', 0, '0.00', 'aktif', '2026-06-02 03:37:43');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `api_health_log`
--
ALTER TABLE `api_health_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `api_request_log`
--
ALTER TABLE `api_request_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `backtracking_log`
--
ALTER TABLE `backtracking_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `logs_transaksi`
--
ALTER TABLE `logs_transaksi`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `pricing_plans`
--
ALTER TABLE `pricing_plans`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nama_paket` (`nama_paket`);

--
-- Indexes for table `registered_apps`
--
ALTER TABLE `registered_apps`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `api_key` (`api_key`),
  ADD KEY `nama_paket` (`nama_paket`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `api_health_log`
--
ALTER TABLE `api_health_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `api_request_log`
--
ALTER TABLE `api_request_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `backtracking_log`
--
ALTER TABLE `backtracking_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `logs_transaksi`
--
ALTER TABLE `logs_transaksi`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `pricing_plans`
--
ALTER TABLE `pricing_plans`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `registered_apps`
--
ALTER TABLE `registered_apps`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `registered_apps`
--
ALTER TABLE `registered_apps`
  ADD CONSTRAINT `registered_apps_ibfk_1` FOREIGN KEY (`nama_paket`) REFERENCES `pricing_plans` (`nama_paket`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
