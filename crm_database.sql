-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 01-10-2025 a las 02:14:26
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

-- =====================================================
-- BASE DE DATOS CORREGIDA PARA WHATSAPP BACKEND CRM
-- =====================================================
-- Este archivo ha sido modificado para incluir TODAS las columnas
-- que el backend realmente necesita según el análisis del código:
--
-- CAMBIOS REALIZADOS:
-- 1. Tabla 'afiliados': Agregadas columnas identidad, observaciones, 
--    contrato_url, disponibilidad_rotativos, transporte_propio
-- 2. Tabla 'users': Agregada columna apellido y updated_at
-- 3. Tabla 'clientes': Agregadas columnas contacto_nombre, sector, observaciones, created_at
-- 4. Contraseñas actualizadas a hash correcto: $2b$12$6fHuo4Qr3.wMxRfpFYe6Euly8UP/bFjZ2eo.rcDnkwE0PGwbZUzwe
-- 5. Datos de usuarios actualizados con apellidos
--
-- USAR ESTE ARCHIVO PARA RECREAR LA BASE DE DATOS COMPLETAMENTE
-- =====================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `whatsapp_backend`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Afiliados`
--

CREATE TABLE `Afiliados` (
  `id_afiliado` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL DEFAULT 1,
  `nombre_completo` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `ciudad` varchar(50) DEFAULT NULL,
  `cargo_solicitado` varchar(100) DEFAULT NULL,
  `experiencia` text DEFAULT NULL,
  `habilidades` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`habilidades`)),
  `puntuacion` int(11) DEFAULT 0,
  `estado` enum('active','pending','hired','rejected') DEFAULT 'active',
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp(),
  `fuente_reclutamiento` varchar(50) DEFAULT NULL,
  `grado_academico` varchar(100) DEFAULT NULL COMMENT 'Grado académico del candidato',
  `disponibilidad` enum('Disponible','No disponible','Trabajando') DEFAULT 'Disponible' COMMENT 'Estado de disponibilidad',
  `cv_url` varchar(500) DEFAULT NULL COMMENT 'URL del CV del candidato',
  `linkedin` varchar(200) DEFAULT NULL COMMENT 'Perfil de LinkedIn',
  `portfolio` varchar(500) DEFAULT NULL COMMENT 'URL del portfolio',
  `skills` text DEFAULT NULL COMMENT 'Habilidades del candidato (separadas por comas)',
  `comentarios` text DEFAULT NULL COMMENT 'Comentarios adicionales sobre el candidato',
  `fecha_nacimiento` date DEFAULT NULL COMMENT 'Fecha de nacimiento',
  `nacionalidad` varchar(50) DEFAULT NULL COMMENT 'Nacionalidad del candidato',
  `identidad` varchar(50) DEFAULT NULL COMMENT 'Número de identidad del candidato',
  `observaciones` text DEFAULT NULL COMMENT 'Observaciones adicionales',
  `contrato_url` varchar(500) DEFAULT NULL COMMENT 'URL del contrato firmado',
  `disponibilidad_rotativos` tinyint(1) DEFAULT 0 COMMENT 'Disponibilidad para turnos rotativos',
  `transporte_propio` tinyint(1) DEFAULT 0 COMMENT 'Cuenta con transporte propio'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Afiliados`
--

INSERT INTO `Afiliados` (`id_afiliado`, `tenant_id`, `nombre_completo`, `email`, `telefono`, `ciudad`, `cargo_solicitado`, `experiencia`, `habilidades`, `puntuacion`, `estado`, `fecha_registro`, `fuente_reclutamiento`, `grado_academico`, `disponibilidad`, `cv_url`, `linkedin`, `portfolio`, `skills`, `comentarios`, `fecha_nacimiento`, `nacionalidad`) VALUES
(1, 1, 'Ana López', 'ana.lopez@email.com', '+52 55 1111 2222', 'Ciudad de México', 'Desarrollador Frontend', '3 años desarrollando con React, TypeScript y Next.js. Experiencia en e-commerce y aplicaciones móviles.', NULL, 85, 'active', '2025-09-20 21:37:28', 'LinkedIn', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(2, 1, 'Carlos Ruiz', 'carlos.ruiz@email.com', '+52 55 3333 4444', 'Guadalajara', 'Desarrollador Backend', '4 años con Python, Flask y Django. Experiencia en microservicios y bases de datos.', NULL, 90, 'active', '2025-09-20 21:37:28', 'Indeed', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(3, 1, 'Laura Martínez', 'laura.martinez@email.com', '+52 55 5555 6666', 'Monterrey', 'Diseñador UX/UI', '2 años diseñando interfaces para aplicaciones web y móviles. Experiencia en design systems.', NULL, 78, 'active', '2025-09-20 21:37:28', 'Behance', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(4, 1, 'Miguel Torres', 'miguel.torres@email.com', '+52 55 7777 8888', 'Ciudad de México', 'Product Manager', '5 años gestionando productos digitales. Experiencia en metodologías ágiles y análisis de datos.', NULL, 92, 'active', '2025-09-20 21:37:28', 'Referido', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(5, 1, 'Sofia Herrera', 'sofia.herrera@email.com', '+52 55 9999 0000', 'Guadalajara', 'Marketing Digital', '3 años en marketing digital con enfoque en SEM y redes sociales. Experiencia en e-commerce.', NULL, 80, 'active', '2025-09-20 21:37:28', 'Facebook', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(6, 1, 'María González Pérez', 'maria.gonzalez@email.com', '+52 55 1234 5678', 'Ciudad de México', 'Desarrolladora Frontend', '5 años en desarrollo de software, especializada en React y Node.js', '{\"tecnologias\": [\"JavaScript\", \"React\", \"Node.js\", \"Python\", \"MySQL\"], \"nivel\": \"Avanzado\", \"certificaciones\": [\"AWS Certified Developer\", \"React Professional\"], \"idiomas\": [\"Espa\\u00f1ol\", \"Ingl\\u00e9s\"]}', 0, 'active', '2025-09-21 01:44:33', 'LinkedIn', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(7, 1, 'Carlos Rodríguez Martínez', 'carlos.rodriguez@email.com', '+52 55 2345 6789', 'Guadalajara', 'Especialista en Marketing Digital', '3 años en marketing digital y gestión de redes sociales', '{\"tecnologias\": [\"Google Analytics\", \"Facebook Ads\", \"SEO\", \"SEM\", \"HubSpot\"], \"nivel\": \"Intermedio\", \"certificaciones\": [\"Google Ads Certified\", \"Facebook Blueprint\"], \"idiomas\": [\"Espa\\u00f1ol\", \"Ingl\\u00e9s\"]}', 0, 'active', '2025-09-21 01:44:33', 'Indeed', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(9, 1, 'Roberto Silva Jiménez', 'roberto.silva@email.com', '+52 55 4567 8901', 'Puebla', 'Ejecutivo de Ventas', '4 años en ventas B2B y gestión de cuentas', '{\"tecnologias\": [\"Salesforce\", \"CRM\", \"Power BI\", \"Excel Avanzado\"], \"nivel\": \"Intermedio\", \"certificaciones\": [\"Salesforce Certified\", \"Microsoft Power BI\"], \"idiomas\": [\"Espa\\u00f1ol\", \"Ingl\\u00e9s\"]}', 0, 'active', '2025-09-21 01:44:33', 'Glassdoor', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(13, 1, 'Diego Ramírez Morales', 'diego.ramirez@email.com', '+52 55 8901 2345', 'León', 'Analista de Logística', '5 años en logística y cadena de suministro', '{\"tecnologias\": [\"SAP\", \"Excel Avanzado\", \"Power BI\", \"SQL\", \"Python\"], \"nivel\": \"Intermedio\", \"certificaciones\": [\"SAP MM Certified\", \"Microsoft Power BI\"], \"idiomas\": [\"Espa\\u00f1ol\", \"Ingl\\u00e9s\"]}', 0, 'active', '2025-09-21 01:44:33', 'Referido', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(14, 1, 'Valentina Cruz Domínguez', 'valentina.cruz@email.com', '+52 55 9012 3456', 'Aguascalientes', 'Especialista en Soporte Técnico', '3 años en atención al cliente y soporte técnico', '{\"tecnologias\": [\"Zendesk\", \"Jira\", \"ServiceNow\", \"Excel\", \"PowerShell\"], \"nivel\": \"Intermedio\", \"certificaciones\": [\"Zendesk Certified\", \"ITIL Foundation\"], \"idiomas\": [\"Espa\\u00f1ol\", \"Ingl\\u00e9s\"]}', 0, 'active', '2025-09-21 01:44:33', 'Indeed', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(15, 1, 'Andrés Mendoza Castro', 'andres.mendoza@email.com', '+52 55 0123 4567', 'Querétaro', 'Desarrollador Backend Senior', '6 años en desarrollo backend y bases de datos', '{\"tecnologias\": [\"Python\", \"Django\", \"PostgreSQL\", \"Docker\", \"AWS\", \"Microservicios\"], \"nivel\": \"Avanzado\", \"certificaciones\": [\"AWS Certified Developer\", \"Django Professional\"], \"idiomas\": [\"Espa\\u00f1ol\", \"Ingl\\u00e9s\", \"Alem\\u00e1n\"]}', 0, 'active', '2025-09-21 01:44:33', 'LinkedIn', NULL, 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(16, 1, 'Alexa Gisselle Sanchez Miranda', 'alexagsanchez26@gmail.com', '+504 96204505', 'Villanueva', NULL, 'Sin experiencia laboral formal. Sin embargo, posee habilidades en servicio al cliente adquiridas en proyectos familiares.', '[\"servicio al cliente\"]', 0, 'active', '2025-09-26 18:03:09', 'CV Upload', 'Bachillerato en Ciencias y Humanidades', 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(17, 1, 'Cristy Vanessa Flores Flores', 'cristyvanessaflores1986@gmail.com', '9823-8498', NULL, NULL, 'COFFEEBEANS: Barista atencion al Cliente, preparación de Bebidas de café (2012-2018).\nSHANTI CUP: Supervisora, Manejo de personal, arqueos de caja (2019-2022).\nlady lee (cafetini): subgerente de tienda, manejo de personal control de inventarios ,arqueos de cajas registradoras y conocimiento de sistema de sap (2022-2024).', '[\"Curso Básico de Barista\", \"Curso de mecanografía\", \"Curso Básico de Computación (Windows\", \"Microsoft Office e Internet)\"]', 0, 'active', '2025-09-26 18:03:09', 'CV Upload', 'Bachiller en Administración de Empresas', 'Disponible', NULL, NULL, NULL, NULL, 'No. de Identidad: 1310-1986-00087\nEdad: 38 años\nEstado Civil: unión libre\nDirección: Col. Valle de sula #1 28 y 29 calle', '1986-01-01', NULL),
(18, 1, 'WILLIAMS RICARDO RUBIO', 'wllllams.rublo1976@gmall.com', '8839 -3250', NULL, 'puesto de trabajo desafiante', 'Gerente de Eventos y Banquetes en Hotel Marriot (septiembre 2018 - junio 2020): Supervisar a Capitanes de Servicio, Proyección para Mejoras en el Servicio y calidad, Manejo de Costos, Manejo de personal.\nCapitán de Eventos y Banquetes en Hotel Intercontinental (junio 2006 - julio 2018): Supervisión de Montajes, Supervisión de los salones y Restaurante, Hacer planillas de personal permanente y Personal Eventual.\nAsistente de A&B en Hotel Honduras Maya (junio 1993 - noviembre 2004): Supervisor de Personal Stewart, Supervisión de Room Service y Mini Bares, Lectura de Hojas de Función y llevarlas a cabalidad.', '[\"Supervisión\", \"Manejo de personal\", \"Manejo de costos\", \"Planificación de eventos\", \"Atención al cliente\", \"Control de inventarios\", \"Facturación de eventos\", \"Manejo Programa Hotelero Opera\", \"Control de Stocks\", \"Dominio y Control en Brifflngs a Empleados en Area de Eventos y Banquetes\", \"Brifflngs a Empleados en Area de Eventos y Banquetes\"]', 0, 'active', '2025-09-27 11:35:33', 'CV Upload', 'Instituto Iberoamericano', 'Disponible', NULL, NULL, NULL, NULL, NULL, NULL, 'Hondureña');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `afiliado_tags`
--

CREATE TABLE `Afiliado_Tags` (
  `id_afiliado` int(11) NOT NULL,
  `id_tag` int(11) NOT NULL,
  `fecha_asignacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `tenant_id` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `calendar_reminders`
--

CREATE TABLE `calendar_reminders` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `date` date NOT NULL,
  `time` time NOT NULL,
  `type` enum('personal','team','general') NOT NULL DEFAULT 'personal',
  `priority` enum('low','medium','high') NOT NULL DEFAULT 'medium',
  `status` enum('pending','completed','cancelled') NOT NULL DEFAULT 'pending',
  `created_by` int(11) NOT NULL,
  `assigned_to` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`assigned_to`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `calendar_reminders`
--

INSERT INTO `calendar_reminders` (`id`, `tenant_id`, `title`, `description`, `date`, `time`, `type`, `priority`, `status`, `created_by`, `assigned_to`, `created_at`, `updated_at`) VALUES
(1, 1, 'Reunión semanal de equipo', 'Revisión de objetivos y metas semanales', '2025-09-25', '09:00:00', 'team', 'high', 'pending', 1, '[1, 2]', '2025-09-25 23:36:57', '2025-09-25 23:36:57'),
(2, 1, 'Seguimiento de candidatos', 'Revisar postulaciones pendientes', '2025-09-26', '14:00:00', 'personal', 'medium', 'pending', 1, '[1]', '2025-09-25 23:36:57', '2025-09-25 23:36:57'),
(3, 1, 'Capacitación de reclutamiento', 'Sesión de capacitación sobre nuevas técnicas', '2025-09-28', '10:00:00', 'general', 'medium', 'pending', 1, '[1, 2, 3]', '2025-09-25 23:36:57', '2025-09-25 23:36:57');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `candidato_tags`
--

CREATE TABLE `candidato_tags` (
  `id_afiliado` int(11) NOT NULL,
  `id_tag` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `candidato_tags`
--

INSERT INTO `candidato_tags` (`id_afiliado`, `id_tag`, `created_at`) VALUES
(1, 3, '2025-09-20 21:37:29'),
(1, 7, '2025-09-20 21:37:29'),
(2, 1, '2025-09-20 21:37:29'),
(2, 4, '2025-09-20 21:37:29'),
(3, 2, '2025-09-20 21:37:29'),
(3, 5, '2025-09-20 21:37:29'),
(4, 1, '2025-09-20 21:37:29'),
(4, 8, '2025-09-20 21:37:29'),
(5, 6, '2025-09-20 21:37:29'),
(5, 7, '2025-09-20 21:37:29');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Clientes`
--

CREATE TABLE `Clientes` (
  `id_cliente` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL DEFAULT 1,
  `empresa` varchar(100) NOT NULL,
  `contacto` varchar(100) NOT NULL,
  `contacto_nombre` varchar(255) DEFAULT NULL COMMENT 'Nombre del contacto principal',
  `email` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `sector` varchar(100) DEFAULT NULL COMMENT 'Sector de la empresa',
  `direccion` text DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `observaciones` text DEFAULT NULL COMMENT 'Observaciones adicionales',
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp(),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Clientes`
--

INSERT INTO `Clientes` (`id_cliente`, `tenant_id`, `empresa`, `contacto`, `email`, `telefono`, `direccion`, `descripcion`, `fecha_registro`) VALUES
(1, 1, 'Empresa Demo', 'Admin Demo', 'admin@demo.com', '+52 55 0000 0000', 'Ciudad de México', NULL, '2025-09-20 21:37:28'),
(2, 1, 'Tech Corp', 'María García', 'maria@techcorp.com', '+52 55 1234 5678', 'Av. Reforma 123, CDMX', 'Empresa de tecnología especializada en desarrollo web', '2025-09-20 21:37:28'),
(3, 1, 'StartupXYZ', 'Juan Pérez', 'juan@startupxyz.com', '+52 55 8765 4321', 'Calle Insurgentes 456, GDL', 'Startup innovadora en fintech', '2025-09-20 21:37:28'),
(4, 1, 'Digital Solutions', 'Ana López', 'ana@digitalsolutions.com', '+52 55 2468 1357', 'Blvd. Constitución 789, MTY', 'Agencia digital con enfoque en UX/UI', '2025-09-20 21:37:28'),
(5, 2, 'Cliente Prueba', 'Contacto Prueba', 'cliente@prueba.com', NULL, NULL, NULL, '2025-09-26 18:35:49');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Contratados`
--

CREATE TABLE `Contratados` (
  `id_contratado` int(11) NOT NULL,
  `id_afiliado` int(11) NOT NULL,
  `id_vacante` int(11) NOT NULL,
  `fecha_contratacion` date NOT NULL,
  `salario_final` decimal(10,2) DEFAULT NULL,
  `tarifa_servicio` decimal(10,2) DEFAULT NULL,
  `monto_pagado` decimal(10,2) DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `tenant_id` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Contratados`
--

INSERT INTO `Contratados` (`id_contratado`, `id_afiliado`, `id_vacante`, `fecha_contratacion`, `salario_final`, `tarifa_servicio`, `monto_pagado`, `created_at`, `tenant_id`) VALUES
(1, 1, 1, '2024-02-01', 25000.00, 5000.00, 5000.00, '2025-09-20 21:37:28', 1),
(2, 3, 3, '2024-02-15', 22000.00, 4000.00, 4000.00, '2025-09-20 21:37:28', 1),
(3, 4, 4, '2024-03-01', 35000.00, 7000.00, 3500.00, '2025-09-20 21:37:28', 1),
(4, 1, 1, '2024-02-01', 25000.00, 5000.00, 5000.00, '2025-09-20 22:32:31', 1),
(5, 2, 2, '2024-02-15', 30000.00, 6000.00, 3000.00, '2025-09-20 22:32:31', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `documentos`
--

CREATE TABLE `documentos` (
  `id_documento` int(11) NOT NULL,
  `id_afiliado` int(11) NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `tipo_documento` varchar(100) DEFAULT NULL,
  `fecha_subida` timestamp NOT NULL DEFAULT current_timestamp(),
  `ruta_archivo` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Email_Templates`
--

CREATE TABLE `Email_Templates` (
  `id_template` int(11) NOT NULL,
  `nombre_plantilla` varchar(100) NOT NULL,
  `asunto` varchar(200) NOT NULL,
  `cuerpo_html` text NOT NULL,
  `id_cliente` int(11) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `tenant_id` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Email_Templates`
--

INSERT INTO `Email_Templates` (`id_template`, `nombre_plantilla`, `asunto`, `cuerpo_html`, `id_cliente`, `created_at`, `tenant_id`) VALUES
(1, 'Bienvenida', 'Bienvenido a nuestro proceso de selección', '<h1>¡Hola {{nombre}}!</h1><p>Gracias por tu interés en nuestra vacante de {{cargo}}.</p>', 1, '2025-09-20 21:37:29', 1),
(2, 'Entrevista', 'Invitación a entrevista', '<h1>Invitación a entrevista</h1><p>Hola {{nombre}}, nos gustaría invitarte a una entrevista para la posición de {{cargo}}.</p>', 1, '2025-09-20 21:37:29', 1),
(3, 'Rechazo', 'Resultado del proceso', '<h1>Resultado del proceso</h1><p>Hola {{nombre}}, gracias por tu tiempo. Hemos decidido continuar con otros candidatos.</p>', 1, '2025-09-20 21:37:29', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Entrevistas`
--

CREATE TABLE `Entrevistas` (
  `id_entrevista` int(11) NOT NULL,
  `id_postulacion` int(11) NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `tipo` enum('Presencial','Virtual','Telefónica') DEFAULT 'Presencial',
  `resultado` enum('Programada','Completada','Cancelada','Reprogramada') DEFAULT 'Programada',
  `notas` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `entrevistador` varchar(255) DEFAULT 'Sin asignar',
  `observaciones` text DEFAULT NULL,
  `tenant_id` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Entrevistas`
--

INSERT INTO `Entrevistas` (`id_entrevista`, `id_postulacion`, `fecha_hora`, `tipo`, `resultado`, `notas`, `created_at`, `entrevistador`, `observaciones`, `tenant_id`) VALUES
(1, 1, '2024-01-15 10:00:00', 'Virtual', 'Completada', 'Excelente entrevista técnica, candidato muy preparado', '2025-09-20 21:37:28', 'Sin asignar', NULL, 1),
(2, 3, '2024-01-20 14:30:00', 'Presencial', 'Completada', 'Portafolio excelente, buena comunicación', '2025-09-20 21:37:28', 'Sin asignar', NULL, 1),
(3, 4, '2024-01-25 16:00:00', 'Virtual', 'Completada', 'Experiencia sólida en gestión de productos', '2025-09-20 21:37:28', 'Sin asignar', NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `errorlogs`
--

CREATE TABLE `errorlogs` (
  `id` int(11) NOT NULL,
  `error_type` varchar(100) NOT NULL,
  `error_message` text NOT NULL,
  `stack_trace` text DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `interviews`
--

CREATE TABLE `interviews` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `candidate_id` int(11) NOT NULL,
  `vacancy_id` int(11) NOT NULL,
  `interview_date` date NOT NULL,
  `interview_time` time NOT NULL,
  `status` enum('scheduled','completed','cancelled','rescheduled') NOT NULL DEFAULT 'scheduled',
  `notes` text DEFAULT NULL,
  `interviewer` varchar(255) DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `interviews`
--

INSERT INTO `interviews` (`id`, `tenant_id`, `candidate_id`, `vacancy_id`, `interview_date`, `interview_time`, `status`, `notes`, `interviewer`, `created_by`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 1, '2025-09-27', '10:00:00', 'scheduled', NULL, 'Juan Pérez', 1, '2025-09-25 23:36:57', '2025-09-25 23:36:57'),
(2, 1, 2, 2, '2025-09-28', '15:30:00', 'scheduled', NULL, 'María González', 1, '2025-09-25 23:36:57', '2025-09-25 23:36:57'),
(3, 1, 3, 1, '2025-09-30', '11:00:00', 'scheduled', NULL, 'Carlos López', 1, '2025-09-25 23:36:57', '2025-09-25 23:36:57');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mensajes_contacto`
--

CREATE TABLE `mensajes_contacto` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `mensaje` text NOT NULL,
  `fecha_recepcion` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado` enum('nuevo','leído','respondido') DEFAULT 'nuevo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `mensajes_contacto`
--

INSERT INTO `mensajes_contacto` (`id`, `nombre`, `email`, `telefono`, `mensaje`, `fecha_recepcion`, `estado`) VALUES
(1, 'Roberto Silva', 'roberto@email.com', '+52 55 1111 3333', 'Hola, me interesa trabajar en su empresa. ¿Tienen vacantes para desarrollador?', '2025-09-20 21:37:29', 'nuevo'),
(2, 'Carmen Vega', 'carmen@email.com', '+52 55 2222 4444', 'Buenos días, soy diseñadora y me gustaría aplicar a alguna posición.', '2025-09-20 21:37:29', 'nuevo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `tipo` varchar(50) NOT NULL,
  `titulo` varchar(255) NOT NULL,
  `mensaje` text DEFAULT NULL,
  `leida` tinyint(1) DEFAULT 0,
  `prioridad` enum('baja','media','alta','urgente') DEFAULT 'media',
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_lectura` timestamp NULL DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `type` varchar(50) DEFAULT 'info',
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `tipo`, `titulo`, `mensaje`, `leida`, `prioridad`, `fecha_creacion`, `fecha_lectura`, `metadata`, `title`, `message`, `type`, `is_read`, `created_at`) VALUES
(1, 1, '', '', NULL, 0, 'media', '2025-09-21 00:21:28', NULL, NULL, 'Bienvenido al CRM', 'Sistema configurado correctamente', 'success', 0, '2025-09-21 00:21:28'),
(2, 1, '', '', NULL, 0, 'media', '2025-09-21 00:21:28', NULL, NULL, 'Nuevos candidatos', 'Tienes 3 nuevos candidatos para revisar', 'info', 0, '2025-09-21 00:21:28'),
(3, 1, '', '', NULL, 0, 'media', '2025-09-21 00:21:28', NULL, NULL, 'Entrevista programada', 'Entrevista con Juan Pérez mañana a las 10:00', 'warning', 0, '2025-09-21 00:21:28');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `posts`
--

CREATE TABLE `posts` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `excerpt` text DEFAULT NULL,
  `content` text NOT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `author` varchar(100) DEFAULT NULL,
  `estado` enum('borrador','publicado','archivado') DEFAULT 'borrador',
  `fecha_publicacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `posts`
--

INSERT INTO `posts` (`id`, `title`, `excerpt`, `content`, `image_url`, `author`, `estado`, `fecha_publicacion`, `created_at`) VALUES
(1, 'Cómo encontrar el mejor talento', 'Guía completa para reclutamiento efectivo', 'El reclutamiento efectivo requiere estrategia y herramientas adecuadas...', NULL, 'Admin', 'publicado', '2025-09-20 21:37:29', '2025-09-20 21:37:29'),
(2, 'Tendencias en RH 2024', 'Las últimas tendencias en recursos humanos', 'Este año vemos importantes cambios en la gestión del talento...', NULL, 'Admin', 'publicado', '2025-09-20 21:37:29', '2025-09-20 21:37:29');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Postulaciones`
--

CREATE TABLE `Postulaciones` (
  `id_postulacion` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL DEFAULT 1,
  `id_afiliado` int(11) NOT NULL,
  `id_vacante` int(11) NOT NULL,
  `fecha_aplicacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado` enum('Pendiente','En Revisión','Entrevistado','Aprobado','Rechazado') DEFAULT 'Pendiente',
  `comentarios` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Postulaciones`
--

INSERT INTO `Postulaciones` (`id_postulacion`, `tenant_id`, `id_afiliado`, `id_vacante`, `fecha_aplicacion`, `estado`, `comentarios`, `created_at`) VALUES
(1, 1, 1, 1, '2025-09-20 21:37:28', '', 'Candidato con excelente perfil técnico', '2025-09-20 21:37:28'),
(2, 1, 2, 2, '2025-09-20 21:37:28', 'Pendiente', 'Experiencia sólida en backend', '2025-09-20 21:37:28'),
(3, 1, 3, 3, '2025-09-20 21:37:28', 'Entrevistado', 'Portafolio impresionante', '2025-09-20 21:37:28'),
(4, 1, 4, 4, '2025-09-20 21:37:28', 'Aprobado', 'Perfecto fit para el rol', '2025-09-20 21:37:28'),
(5, 1, 5, 5, '2025-09-20 21:37:28', 'Pendiente', 'Experiencia relevante en marketing', '2025-09-20 21:37:28'),
(6, 1, 7, 1, '2025-09-24 16:57:08', '', 'ah', '2025-09-24 16:57:08'),
(7, 1, 1, 2, '2025-09-24 17:39:11', '', '', '2025-09-24 17:39:11'),
(8, 1, 14, 1, '2025-09-24 17:41:06', '', '', '2025-09-24 17:41:06'),
(9, 1, 6, 1, '2025-09-24 17:45:00', '', '', '2025-09-24 17:45:00'),
(10, 1, 6, 2, '2025-09-24 17:57:27', '', '', '2025-09-24 17:57:27'),
(11, 1, 14, 6, '2025-09-24 17:57:51', '', '', '2025-09-24 17:57:51'),
(12, 1, 5, 2, '2025-09-24 18:31:34', '', '', '2025-09-24 18:31:34'),
(13, 1, 15, 2, '2025-09-25 11:38:48', '', '', '2025-09-25 11:38:48'),
(14, 1, 6, 4, '2025-09-25 14:29:12', '', '', '2025-09-25 14:29:12');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Roles`
--

CREATE TABLE `Roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `permisos` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`permisos`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Roles`
--

INSERT INTO `Roles` (`id`, `nombre`, `descripcion`, `permisos`, `created_at`) VALUES
(1, 'Administrador', 'Acceso completo al sistema', NULL, '2025-09-20 21:37:27'),
(2, 'Reclutador', 'Gestión de candidatos y vacantes', NULL, '2025-09-20 21:37:27'),
(3, 'Visualizador', 'Solo lectura', NULL, '2025-09-20 21:37:27');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Tags`
--

CREATE TABLE `Tags` (
  `id_tag` int(11) NOT NULL,
  `nombre_tag` varchar(50) NOT NULL,
  `id_cliente` int(11) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `tenant_id` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Tags`
--

INSERT INTO `Tags` (`id_tag`, `nombre_tag`, `id_cliente`, `created_at`, `tenant_id`) VALUES
(1, 'Senior', 1, '2025-09-20 21:37:29', 1),
(2, 'Junior', 1, '2025-09-20 21:37:29', 1),
(3, 'React', 1, '2025-09-20 21:37:29', 1),
(4, 'Python', 1, '2025-09-20 21:37:29', 1),
(5, 'Diseño', 1, '2025-09-20 21:37:29', 1),
(6, 'Marketing', 1, '2025-09-20 21:37:29', 1),
(7, 'Remoto', 1, '2025-09-20 21:37:29', 1),
(8, 'Presencial', 1, '2025-09-20 21:37:29', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Tenants`
--

CREATE TABLE `Tenants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_empresa` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `contacto_principal` varchar(100) DEFAULT NULL,
  `email_contacto` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `direccion` text DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Tenants`
--

INSERT INTO `Tenants` (`id`, `nombre_empresa`, `descripcion`, `contacto_principal`, `email_contacto`, `telefono`, `direccion`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES
(1, 'Empresa Demo', 'Empresa de reclutamiento demo', 'Admin Demo', 'admin@demo.com', NULL, NULL, 1, '2025-09-26 18:27:36', '2025-09-26 18:27:36'),
(2, 'Empresa Prueba', 'Empresa de prueba para testing', 'Admin Prueba', 'admin@prueba.com', NULL, NULL, 1, '2025-09-26 18:35:49', '2025-09-26 18:35:49');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `useractivitylog`
--

CREATE TABLE `useractivitylog` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `activity_type` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `useractivitylog`
--

INSERT INTO `useractivitylog` (`id`, `user_id`, `activity_type`, `description`, `ip_address`, `user_agent`, `created_at`) VALUES
(1, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T18:02:07.025548\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-20 23:02:07'),
(2, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T18:11:30.836462\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-20 23:11:30'),
(3, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T18:17:37.782108\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-20 23:17:37'),
(4, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T18:19:00.131162\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-20 23:19:00'),
(5, 4, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T21:04:08.806478\", \"ip_address\": \"127.0.0.1\", \"email\": \"agencia.henmir@gmail.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 4}', '127.0.0.1', 'Desconocido', '2025-09-21 02:04:08'),
(6, 4, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T21:09:42.231153\", \"ip_address\": \"127.0.0.1\", \"email\": \"agencia.henmir@gmail.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 4}', '127.0.0.1', 'Desconocido', '2025-09-21 02:09:42'),
(7, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T21:17:38.246641\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-21 02:17:38'),
(8, 4, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T23:45:32.688431\", \"ip_address\": \"127.0.0.1\", \"email\": \"agencia.henmir@gmail.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 4}', '127.0.0.1', 'Desconocido', '2025-09-21 04:45:32'),
(9, 4, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-20T23:46:22.592160\", \"ip_address\": \"127.0.0.1\", \"email\": \"agencia.henmir@gmail.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 4}', '127.0.0.1', 'Desconocido', '2025-09-21 04:46:22'),
(10, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-21T23:11:52.187002\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-22 04:11:52'),
(11, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-22T13:12:38.041624\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-22 18:12:38'),
(12, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-22T21:44:32.076272\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-23 02:44:32'),
(13, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-23T05:43:17.802452\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-23 10:43:17'),
(14, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-23T05:43:50.854346\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-23 10:43:50'),
(15, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-23T05:58:00.907167\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-23 10:58:00'),
(16, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-23T13:29:39.772384\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-23 18:29:39'),
(17, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-23T19:04:24.890767\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 00:04:24'),
(18, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-23T19:43:12.010995\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 00:43:12'),
(19, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-24T07:37:18.165046\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 12:37:18'),
(20, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-24T08:01:21.774702\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 13:01:21'),
(21, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-24T09:37:18.270352\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 14:37:18'),
(22, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-24T12:12:40.753374\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 17:12:40'),
(23, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-24T12:38:57.430643\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-24 17:38:57'),
(24, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T06:38:10.652729\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 11:38:10'),
(25, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T07:14:36.352940\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 12:14:36'),
(26, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T07:47:53.955718\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 12:47:53'),
(27, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T07:48:48.408515\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 12:48:48'),
(28, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T07:49:58.702100\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 12:49:58'),
(29, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T07:58:44.122394\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 12:58:44'),
(30, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T07:59:44.121051\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 12:59:44'),
(31, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T08:02:00.092278\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 13:02:00'),
(32, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T08:02:52.430692\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 13:02:52'),
(33, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T08:04:31.839662\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 13:04:31'),
(34, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T08:12:02.392897\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 13:12:02'),
(35, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T08:13:05.015151\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 13:13:05'),
(36, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T08:22:03.486730\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 13:22:03'),
(37, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T09:21:39.286568\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 14:21:39'),
(38, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T09:23:04.602041\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 14:23:04'),
(39, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T11:00:24.254261\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 16:00:24'),
(40, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T11:02:17.098949\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 16:02:17'),
(41, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T12:32:53.729896\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 17:32:53'),
(42, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T12:33:19.090594\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 17:33:19'),
(43, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T12:33:34.876337\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 17:33:34'),
(44, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:07:55.435252\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:07:55'),
(45, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:21:51.408611\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:21:51'),
(46, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:48:10.458711\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:48:10'),
(47, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:54:02.957223\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:54:02'),
(48, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:55:37.936719\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:55:37'),
(49, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:56:53.498532\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:56:53'),
(50, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T13:58:52.573735\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 18:58:52'),
(51, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:35:01.874167\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:35:01'),
(52, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:35:05.936952\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:35:05'),
(53, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:35:27.687629\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:35:27'),
(54, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:36:07.274879\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:36:07'),
(55, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:39:03.550232\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:39:03'),
(56, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:41:41.462034\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:41:41'),
(57, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T14:52:32.449030\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 19:52:32'),
(58, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T15:29:55.093657\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 20:29:55'),
(59, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T15:39:42.239510\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 20:39:42'),
(60, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T15:46:01.515265\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 20:46:01'),
(61, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T15:46:20.798931\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 20:46:20'),
(62, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T15:46:45.230146\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 20:46:45'),
(63, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T16:09:09.468362\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 21:09:09'),
(64, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T16:24:12.232671\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 21:24:12'),
(65, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T16:54:08.199874\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 21:54:08'),
(66, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T17:37:15.371763\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 22:37:15'),
(67, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T17:43:09.408206\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 22:43:09'),
(68, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T17:47:29.095984\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 22:47:29'),
(69, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:14:43.949251\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:14:43'),
(70, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:23:44.911808\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:23:44'),
(71, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:40:15.321714\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:40:15'),
(72, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:40:22.339929\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:40:22'),
(73, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:43:49.680920\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:43:49'),
(74, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:45:17.752874\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:45:17'),
(75, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:48:19.509010\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:48:19'),
(76, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:50:03.396621\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:50:03'),
(77, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:51:46.778881\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:51:46'),
(78, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:55:51.347979\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:55:51'),
(79, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:58:48.396676\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:58:48'),
(80, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T18:59:44.974967\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-25 23:59:44'),
(81, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:00:52.238421\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:00:52'),
(82, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:12:23.795115\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:12:23'),
(83, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:16:40.104506\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:16:40'),
(84, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:17:02.154964\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:17:02'),
(85, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:17:43.094651\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:17:43'),
(86, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:18:03.149816\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:18:03'),
(87, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:20:54.813786\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:20:54'),
(88, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:21:51.834623\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:21:51'),
(89, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:22:15.823031\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:22:15'),
(90, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T19:56:19.376339\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 00:56:19'),
(91, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T20:09:49.067792\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 01:09:49'),
(92, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T20:14:59.735977\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 01:14:59'),
(93, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T20:19:08.177104\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 01:19:08'),
(94, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T20:25:40.667068\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 01:25:40'),
(95, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T20:34:50.302013\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 01:34:50'),
(96, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T22:20:23.808377\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 03:20:23'),
(97, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T22:22:08.229837\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 03:22:08'),
(98, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-25T22:31:57.498631\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 03:31:57'),
(99, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:27:05.535206\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:27:05'),
(100, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:28:26.051843\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:28:26'),
(101, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:33:20.985456\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:33:20'),
(102, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:39:10.593464\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:39:10'),
(103, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:45:50.070721\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:45:50'),
(104, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:51:05.727497\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:51:05'),
(105, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:52:47.425914\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:52:47'),
(106, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:54:30.752717\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:54:30'),
(107, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T11:55:12.131645\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 16:55:12'),
(108, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:02:51.164480\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:02:51'),
(109, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:07:38.793131\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:07:38'),
(110, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:12:06.516827\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:12:06'),
(111, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:13:57.996411\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:13:57'),
(112, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:15:56.492243\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:15:56'),
(113, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:22:59.360803\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:22:59'),
(114, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:24:02.668826\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:24:02'),
(115, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:27:39.896723\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:27:39'),
(116, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:38:24.777964\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:38:24'),
(117, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:39:26.846061\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:39:26'),
(118, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:46:09.710810\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:46:09'),
(119, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:46:53.163574\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:46:53'),
(120, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:49:59.288610\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:49:59'),
(121, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:51:39.939087\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:51:39'),
(122, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:57:59.132771\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:57:59'),
(123, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T12:59:08.655218\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 17:59:08'),
(124, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T13:02:44.749792\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 18:02:44'),
(125, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T13:04:04.098532\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-26 18:04:04'),
(126, 1, 'login_success', '{\"email\": \"admin@crm.com\", \"ip_address\": \"127.0.0.1\", \"user_agent\": \"python-requests/2.28.1\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'python-requests/2.28.1', '2025-09-26 22:17:24'),
(127, 1, 'login_success', '{\"email\": \"admin@crm.com\", \"ip_address\": \"127.0.0.1\", \"user_agent\": \"python-requests/2.28.1\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'python-requests/2.28.1', '2025-09-26 22:17:37'),
(128, 1, 'login_success', '{\"email\": \"admin@crm.com\", \"ip_address\": \"127.0.0.1\", \"user_agent\": \"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36', '2025-09-26 22:17:57'),
(129, 1, 'login_success', '{\"email\": \"admin@crm.com\", \"ip_address\": \"127.0.0.1\", \"user_agent\": \"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36', '2025-09-26 22:53:36'),
(130, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:09:30.924110\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:09:30'),
(131, 2, 'login_failed', '{\"action\": \"login_failed\", \"timestamp\": \"2025-09-26T20:09:33.392971\", \"ip_address\": \"127.0.0.1\", \"email\": \"reclutador@crm.com\", \"user_agent\": \"Desconocido\", \"success\": false, \"details\": {\"reason\": \"Contraseña incorrecta\"}, \"user_id\": 2}', '127.0.0.1', 'Desconocido', '2025-09-27 01:09:33'),
(132, 5, 'login_failed', '{\"action\": \"login_failed\", \"timestamp\": \"2025-09-26T20:09:37.068347\", \"ip_address\": \"127.0.0.1\", \"email\": \"prueba@prueba.com\", \"user_agent\": \"Desconocido\", \"success\": false, \"details\": {\"reason\": \"Contraseña incorrecta\"}, \"user_id\": 5}', '127.0.0.1', 'Desconocido', '2025-09-27 01:09:37'),
(133, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:11:01.209191\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:11:01'),
(134, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:12:24.288940\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:12:24'),
(135, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:12:50.436214\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:12:50'),
(136, 5, 'login_failed', '{\"action\": \"login_failed\", \"timestamp\": \"2025-09-26T20:12:52.530562\", \"ip_address\": \"127.0.0.1\", \"email\": \"prueba@prueba.com\", \"user_agent\": \"Desconocido\", \"success\": false, \"details\": {\"reason\": \"Contraseña incorrecta\"}, \"user_id\": 5}', '127.0.0.1', 'Desconocido', '2025-09-27 01:12:52'),
(137, 5, 'login_failed', '{\"action\": \"login_failed\", \"timestamp\": \"2025-09-26T20:14:10.607418\", \"ip_address\": \"127.0.0.1\", \"email\": \"prueba@prueba.com\", \"user_agent\": \"Desconocido\", \"success\": false, \"details\": {\"reason\": \"Contraseña incorrecta\"}, \"user_id\": 5}', '127.0.0.1', 'Desconocido', '2025-09-27 01:14:10'),
(138, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:15:31.967476\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:15:31'),
(139, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:21:16.328812\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:21:16'),
(140, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:33:50.939511\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:33:50'),
(141, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:42:27.289918\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:42:27'),
(142, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-26T20:49:04.326197\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 01:49:04'),
(143, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T06:26:31.584424\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 11:26:31'),
(144, 3, 'login_failed', '{\"action\": \"login_failed\", \"timestamp\": \"2025-09-27T13:47:49.705296\", \"ip_address\": \"127.0.0.1\", \"email\": \"test@test.com\", \"user_agent\": \"Desconocido\", \"success\": false, \"details\": {\"reason\": \"Contraseña incorrecta\"}, \"user_id\": 3}', '127.0.0.1', 'Desconocido', '2025-09-27 18:47:49'),
(145, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T13:48:48.180445\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 18:48:48'),
(146, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T13:50:33.165291\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 18:50:33'),
(147, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T13:51:27.562692\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 18:51:27'),
(148, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T13:52:48.560361\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 18:52:48'),
(149, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T14:15:44.544455\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 19:15:44'),
(150, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T14:18:30.270909\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 19:18:30'),
(151, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T14:19:32.051364\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 19:19:32'),
(152, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T14:21:15.005360\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 19:21:15'),
(153, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T14:48:08.380227\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 19:48:08'),
(154, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T15:01:19.473912\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 20:01:19'),
(155, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T15:01:50.068674\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 20:01:50'),
(156, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T15:02:15.751683\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 20:02:15'),
(157, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T15:21:48.303868\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 20:21:48'),
(158, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T15:56:17.280313\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 20:56:17'),
(159, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T15:58:11.589675\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 20:58:11'),
(160, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:10:22.174638\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:10:22'),
(161, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:17:12.987831\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:17:12'),
(162, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:25:51.349821\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:25:51');
INSERT INTO `useractivitylog` (`id`, `user_id`, `activity_type`, `description`, `ip_address`, `user_agent`, `created_at`) VALUES
(163, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:34:24.542547\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:34:24'),
(164, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:46:53.428564\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:46:53'),
(165, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:52:28.811941\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:52:28'),
(166, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:52:35.320164\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:52:35'),
(167, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T16:54:45.893545\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 21:54:45'),
(168, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T17:05:55.393697\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 22:05:55'),
(169, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T17:07:37.466247\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 22:07:37'),
(170, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T17:08:04.711779\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 22:08:04'),
(171, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T17:20:54.187662\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 22:20:54'),
(172, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T17:22:54.793076\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 22:22:54'),
(173, 1, 'login_success', '{\"action\": \"login_success\", \"timestamp\": \"2025-09-27T17:37:24.968670\", \"ip_address\": \"127.0.0.1\", \"email\": \"admin@crm.com\", \"user_agent\": \"Desconocido\", \"success\": true, \"details\": {}, \"user_id\": 1}', '127.0.0.1', 'Desconocido', '2025-09-27 22:37:24');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Users`
--

CREATE TABLE `Users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` int NOT NULL DEFAULT 1,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) DEFAULT NULL COMMENT 'Apellido del usuario',
  `telefono` varchar(20) DEFAULT NULL,
  `rol_id` int DEFAULT 2,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `tenant_id` (`tenant_id`),
  KEY `rol_id` (`rol_id`),
  CONSTRAINT `Users_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `Users_ibfk_2` FOREIGN KEY (`rol_id`) REFERENCES `Roles` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Users`
--

INSERT INTO `Users` (`id`, `tenant_id`, `username`, `email`, `password_hash`, `nombre`, `apellido`, `telefono`, `rol_id`, `activo`, `fecha_creacion`) VALUES
(1, 1, 'admin', 'admin@crm.com', '$2b$12$6fHuo4Qr3.wMxRfpFYe6Euly8UP/bFjZ2eo.rcDnkwE0PGwbZUzwe', 'Admin', 'Sistema', NULL, 1, 1, '2025-09-20 21:37:28'),
(2, 1, 'reclutador', 'reclutador@crm.com', '$2b$12$6fHuo4Qr3.wMxRfpFYe6Euly8UP/bFjZ2eo.rcDnkwE0PGwbZUzwe', 'Reclutador', 'Usuario', NULL, 2, 1, '2025-09-20 21:37:28'),
(3, 1, 'test', 'test@test.com', '$2b$12$6fHuo4Qr3.wMxRfpFYe6Euly8UP/bFjZ2eo.rcDnkwE0PGwbZUzwe', 'Usuario', 'Test', NULL, 1, 1, '2025-09-20 21:37:28'),
(4, 1, 'agencia', 'agencia.henmir@gmail.com', '$2b$12$6fHuo4Qr3.wMxRfpFYe6Euly8UP/bFjZ2eo.rcDnkwE0PGwbZUzwe', 'Agencia', 'Henmir', NULL, 2, 1, '2025-09-20 21:55:47'),
(5, 2, 'prueba_user', 'prueba@prueba.com', '$2b$12$6fHuo4Qr3.wMxRfpFYe6Euly8UP/bFjZ2eo.rcDnkwE0PGwbZUzwe', 'Usuario', 'Prueba', NULL, 2, 1, '2025-09-26 18:35:49');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `UserSessions`
--

CREATE TABLE `UserSessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token_id` varchar(500) NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `expira` timestamp NULL DEFAULT NULL,
  `creado_en` timestamp NULL DEFAULT NULL,
  `tenant_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `tenant_id` (`tenant_id`),
  CONSTRAINT `UserSessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `UserSessions_ibfk_2` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `UserSessions`
--

INSERT INTO `UserSessions` (`id`, `user_id`, `token_id`, `ip_address`, `user_agent`, `expira`, `creado_en`, `tenant_id`) VALUES
(1, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJjbGllbnRlX2lkIjoxLCJjbGllbnRlX25vbWJyZSI6IkVtcHJlc2EgRGVtbyIsImV4cCI6MTc1ODQzODEyNiwianRpIjoiZDEzODRiNTgtNDJmNy00OGYzLT', '127.0.0.1', 'Desconocido', '2025-09-21 12:02:06', '2025-09-20 23:02:06', 1),
(2, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJjbGllbnRlX2lkIjoxLCJjbGllbnRlX25vbWJyZSI6IkVtcHJlc2EgRGVtbyIsImV4cCI6MTc1ODQzODY5MCwianRpIjoiMjI1N2YyN2ItMTBiZC00ZDU5LT', '127.0.0.1', 'Desconocido', '2025-09-21 12:11:30', '2025-09-20 23:11:30', 1),
(3, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NDM5MDU3LCJqdGkiOiIxZGU4ZD', '127.0.0.1', 'Desconocido', '2025-09-21 12:17:37', '2025-09-20 23:17:37', 1),
(4, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NDM5MTQwLCJqdGkiOiJiYThlYz', '127.0.0.1', 'Desconocido', '2025-09-21 12:19:00', '2025-09-20 23:19:00', 1),
(5, 4, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJlbWFpbCI6ImFnZW5jaWEuaGVubWlyQGdtYWlsLmNvbSIsInJvbCI6IlJlY2x1dGFkb3IiLCJwZXJtaXNvcyI6e30sInRlbmFudF9pZCI6MSwiY2xpZW50ZV9pZCI6MSwiY2xpZW50ZV9ub21icmUiOiJFbXByZXNhIERlbW8iLCJleHAiOjE3NTg0NDkwNDgsImp0aS', '127.0.0.1', 'Desconocido', '2025-09-21 15:04:08', '2025-09-21 02:04:08', 1),
(6, 4, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJlbWFpbCI6ImFnZW5jaWEuaGVubWlyQGdtYWlsLmNvbSIsInJvbCI6IlJlY2x1dGFkb3IiLCJwZXJtaXNvcyI6e30sInRlbmFudF9pZCI6MSwiY2xpZW50ZV9pZCI6MSwiY2xpZW50ZV9ub21icmUiOiJFbXByZXNhIERlbW8iLCJleHAiOjE3NTg0NDkzODIsImp0aS', '127.0.0.1', 'Desconocido', '2025-09-21 15:09:42', '2025-09-21 02:09:42', 1),
(7, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NDQ5ODU4LCJqdGkiOiJhMTcxZD', '127.0.0.1', 'Desconocido', '2025-09-21 15:17:38', '2025-09-21 02:17:38', 1),
(8, 4, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJlbWFpbCI6ImFnZW5jaWEuaGVubWlyQGdtYWlsLmNvbSIsInJvbCI6IlJlY2x1dGFkb3IiLCJwZXJtaXNvcyI6e30sInRlbmFudF9pZCI6MSwiY2xpZW50ZV9pZCI6MSwiY2xpZW50ZV9ub21icmUiOiJFbXByZXNhIERlbW8iLCJleHAiOjE3NTg0NTg3MzIsImp0aS', '127.0.0.1', 'Desconocido', '2025-09-21 17:45:32', '2025-09-21 04:45:32', 1),
(9, 4, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJlbWFpbCI6ImFnZW5jaWEuaGVubWlyQGdtYWlsLmNvbSIsInJvbCI6IlJlY2x1dGFkb3IiLCJwZXJtaXNvcyI6e30sInRlbmFudF9pZCI6MSwiY2xpZW50ZV9pZCI6MSwiY2xpZW50ZV9ub21icmUiOiJFbXByZXNhIERlbW8iLCJleHAiOjE3NTg0NTg3ODIsImp0aS', '127.0.0.1', 'Desconocido', '2025-09-21 17:46:22', '2025-09-21 04:46:22', 1),
(10, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NTQzMTEyLCJqdGkiOiJmMjE5MW', '127.0.0.1', 'Desconocido', '2025-09-22 17:11:52', '2025-09-22 04:11:52', 1),
(11, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NTkzNTU3LCJqdGkiOiI0YmRlOD', '127.0.0.1', 'Desconocido', '2025-09-23 07:12:37', '2025-09-22 18:12:37', 1),
(12, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NjI0MjcxLCJqdGkiOiIxNmQ3M2', '127.0.0.1', 'Desconocido', '2025-09-23 15:44:31', '2025-09-23 02:44:31', 1),
(13, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NjUyOTk3LCJqdGkiOiJkYTczMT', '127.0.0.1', 'Desconocido', '2025-09-23 23:43:17', '2025-09-23 10:43:17', 1),
(14, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NjUzMDMwLCJqdGkiOiJiMmI3OT', '127.0.0.1', 'Desconocido', '2025-09-23 23:43:50', '2025-09-23 10:43:50', 1),
(15, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NjUzODgwLCJqdGkiOiI0NWNiNj', '127.0.0.1', 'Desconocido', '2025-09-23 23:58:00', '2025-09-23 10:58:00', 1),
(16, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NjgwOTc5LCJqdGkiOiIxNzEzMj', '127.0.0.1', 'Desconocido', '2025-09-24 07:29:39', '2025-09-23 18:29:39', 1),
(17, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzAxMDY0LCJqdGkiOiIyYjJiYT', '127.0.0.1', 'Desconocido', '2025-09-24 13:04:24', '2025-09-24 00:04:24', 1),
(18, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzAzMzkxLCJqdGkiOiJkM2MwOW', '127.0.0.1', 'Desconocido', '2025-09-24 13:43:11', '2025-09-24 00:43:11', 1),
(19, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzQ2MjM3LCJqdGkiOiIyOTgzNj', '127.0.0.1', 'Desconocido', '2025-09-25 01:37:17', '2025-09-24 12:37:17', 1),
(20, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzQ3NjgxLCJqdGkiOiJhNWZkZT', '127.0.0.1', 'Desconocido', '2025-09-25 02:01:21', '2025-09-24 13:01:21', 1),
(21, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzUzNDM4LCJqdGkiOiJiOGVlOT', '127.0.0.1', 'Desconocido', '2025-09-25 03:37:18', '2025-09-24 14:37:18', 1),
(22, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzYyNzYwLCJqdGkiOiI1YmQ3Mj', '127.0.0.1', 'Desconocido', '2025-09-25 06:12:40', '2025-09-24 17:12:40', 1),
(23, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4NzY0MzM3LCJqdGkiOiJkZDcwYW', '127.0.0.1', 'Desconocido', '2025-09-25 06:38:57', '2025-09-24 17:38:57', 1),
(24, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODI5MDkwLCJqdGkiOiIwZmYwYz', '127.0.0.1', 'Desconocido', '2025-09-26 00:38:10', '2025-09-25 11:38:10', 1),
(25, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODMxMjc2LCJqdGkiOiI3NmM4MD', '127.0.0.1', 'Desconocido', '2025-09-26 01:14:36', '2025-09-25 12:14:36', 1),
(26, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODMzMjczLCJqdGkiOiJhZDY5Zm', '127.0.0.1', 'Desconocido', '2025-09-26 01:47:53', '2025-09-25 12:47:53', 1),
(27, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODMzMzI4LCJqdGkiOiJjYzcyN2', '127.0.0.1', 'Desconocido', '2025-09-26 01:48:48', '2025-09-25 12:48:48', 1),
(28, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODMzMzk4LCJqdGkiOiJlMmFmZm', '127.0.0.1', 'Desconocido', '2025-09-26 01:49:58', '2025-09-25 12:49:58', 1),
(29, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODMzOTI0LCJqdGkiOiJjN2EyNW', '127.0.0.1', 'Desconocido', '2025-09-26 01:58:44', '2025-09-25 12:58:44', 1),
(30, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODMzOTg0LCJqdGkiOiIzYmFhOT', '127.0.0.1', 'Desconocido', '2025-09-26 01:59:44', '2025-09-25 12:59:44', 1),
(31, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM0MTE5LCJqdGkiOiI4YTNiMz', '127.0.0.1', 'Desconocido', '2025-09-26 02:01:59', '2025-09-25 13:01:59', 1),
(32, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM0MTcyLCJqdGkiOiI1NmJiZG', '127.0.0.1', 'Desconocido', '2025-09-26 02:02:52', '2025-09-25 13:02:52', 1),
(33, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM0MjcxLCJqdGkiOiIyZmUzY2', '127.0.0.1', 'Desconocido', '2025-09-26 02:04:31', '2025-09-25 13:04:31', 1),
(34, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM0NzIyLCJqdGkiOiI3NDliNG', '127.0.0.1', 'Desconocido', '2025-09-26 02:12:02', '2025-09-25 13:12:02', 1),
(35, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM0Nzg0LCJqdGkiOiIyNzM2MT', '127.0.0.1', 'Desconocido', '2025-09-26 02:13:04', '2025-09-25 13:13:04', 1),
(36, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM1MzIzLCJqdGkiOiJkN2QzYj', '127.0.0.1', 'Desconocido', '2025-09-26 02:22:03', '2025-09-25 13:22:03', 1),
(37, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM4ODk5LCJqdGkiOiJjNmU5MG', '127.0.0.1', 'Desconocido', '2025-09-26 03:21:39', '2025-09-25 14:21:39', 1),
(38, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODM4OTg0LCJqdGkiOiIwMTFhYj', '127.0.0.1', 'Desconocido', '2025-09-26 03:23:04', '2025-09-25 14:23:04', 1),
(39, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODQ0ODI0LCJqdGkiOiIxMGQyMT', '127.0.0.1', 'Desconocido', '2025-09-26 05:00:24', '2025-09-25 16:00:24', 1),
(40, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODQ0OTM2LCJqdGkiOiI1OWRhNj', '127.0.0.1', 'Desconocido', '2025-09-26 05:02:16', '2025-09-25 16:02:16', 1),
(41, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODUwMzczLCJqdGkiOiIzYWNkZT', '127.0.0.1', 'Desconocido', '2025-09-26 06:32:53', '2025-09-25 17:32:53', 1),
(42, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODUwMzk5LCJqdGkiOiJkNjBhYz', '127.0.0.1', 'Desconocido', '2025-09-26 06:33:19', '2025-09-25 17:33:19', 1),
(43, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODUwNDE0LCJqdGkiOiIxN2I3MD', '127.0.0.1', 'Desconocido', '2025-09-26 06:33:34', '2025-09-25 17:33:34', 1),
(44, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODUyNDc1LCJqdGkiOiI0ZWFiYj', '127.0.0.1', 'Desconocido', '2025-09-26 07:07:55', '2025-09-25 18:07:55', 1),
(45, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODUzMzExLCJqdGkiOiJhODNiZj', '127.0.0.1', 'Desconocido', '2025-09-26 07:21:51', '2025-09-25 18:21:51', 1),
(46, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU0ODkwLCJqdGkiOiIxMTcxNW', '127.0.0.1', 'Desconocido', '2025-09-26 07:48:10', '2025-09-25 18:48:10', 1),
(47, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU1MjQyLCJqdGkiOiJlYmEzMG', '127.0.0.1', 'Desconocido', '2025-09-26 07:54:02', '2025-09-25 18:54:02', 1),
(48, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU1MzM3LCJqdGkiOiI4MzcxNT', '127.0.0.1', 'Desconocido', '2025-09-26 07:55:37', '2025-09-25 18:55:37', 1),
(49, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU1NDEzLCJqdGkiOiJmYTNkNj', '127.0.0.1', 'Desconocido', '2025-09-26 07:56:53', '2025-09-25 18:56:53', 1),
(50, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU1NTMyLCJqdGkiOiJmNzEyNT', '127.0.0.1', 'Desconocido', '2025-09-26 07:58:52', '2025-09-25 18:58:52', 1),
(51, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU3NzAxLCJqdGkiOiI4ODdmYT', '127.0.0.1', 'Desconocido', '2025-09-26 08:35:01', '2025-09-25 19:35:01', 1),
(52, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU3NzA1LCJqdGkiOiJjNDIzMD', '127.0.0.1', 'Desconocido', '2025-09-26 08:35:05', '2025-09-25 19:35:05', 1),
(53, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU3NzI3LCJqdGkiOiI2ZTRhMW', '127.0.0.1', 'Desconocido', '2025-09-26 08:35:27', '2025-09-25 19:35:27', 1),
(54, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU3NzY3LCJqdGkiOiIyZmJkMD', '127.0.0.1', 'Desconocido', '2025-09-26 08:36:07', '2025-09-25 19:36:07', 1),
(55, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU3OTQzLCJqdGkiOiIzZmVmNm', '127.0.0.1', 'Desconocido', '2025-09-26 08:39:03', '2025-09-25 19:39:03', 1),
(56, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU4MTAxLCJqdGkiOiJlYzkwOD', '127.0.0.1', 'Desconocido', '2025-09-26 08:41:41', '2025-09-25 19:41:41', 1),
(57, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODU4NzUyLCJqdGkiOiI5N2I1OT', '127.0.0.1', 'Desconocido', '2025-09-26 08:52:32', '2025-09-25 19:52:32', 1),
(58, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODYwOTk1LCJqdGkiOiIzNTJlMj', '127.0.0.1', 'Desconocido', '2025-09-26 09:29:55', '2025-09-25 20:29:55', 1),
(59, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODYxNTgyLCJqdGkiOiIxY2FlND', '127.0.0.1', 'Desconocido', '2025-09-26 09:39:42', '2025-09-25 20:39:42', 1),
(60, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODYxOTYxLCJqdGkiOiI0YzBiMD', '127.0.0.1', 'Desconocido', '2025-09-26 09:46:01', '2025-09-25 20:46:01', 1),
(61, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODYxOTgwLCJqdGkiOiJmMWI2Mm', '127.0.0.1', 'Desconocido', '2025-09-26 09:46:20', '2025-09-25 20:46:20', 1),
(62, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODYyMDA1LCJqdGkiOiI0NmMwZG', '127.0.0.1', 'Desconocido', '2025-09-26 09:46:45', '2025-09-25 20:46:45', 1),
(63, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODYzMzQ5LCJqdGkiOiJhZGYwNz', '127.0.0.1', 'Desconocido', '2025-09-26 10:09:09', '2025-09-25 21:09:09', 1),
(64, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODY0MjUxLCJqdGkiOiJhNDM0OG', '127.0.0.1', 'Desconocido', '2025-09-26 10:24:11', '2025-09-25 21:24:11', 1),
(65, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODY2MDQ4LCJqdGkiOiI3YzQ0ZT', '127.0.0.1', 'Desconocido', '2025-09-26 10:54:08', '2025-09-25 21:54:08', 1),
(66, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODY4NjM1LCJqdGkiOiIxNDFmMj', '127.0.0.1', 'Desconocido', '2025-09-26 11:37:15', '2025-09-25 22:37:15', 1),
(67, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODY4OTg5LCJqdGkiOiIyNzJiMD', '127.0.0.1', 'Desconocido', '2025-09-26 11:43:09', '2025-09-25 22:43:09', 1),
(68, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODY5MjQ5LCJqdGkiOiJkYTE4Ym', '127.0.0.1', 'Desconocido', '2025-09-26 11:47:29', '2025-09-25 22:47:29', 1),
(69, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcwODgzLCJqdGkiOiI0Mjk2ZD', '127.0.0.1', 'Desconocido', '2025-09-26 12:14:43', '2025-09-25 23:14:43', 1),
(70, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcxNDI0LCJqdGkiOiIxMDIxM2', '127.0.0.1', 'Desconocido', '2025-09-26 12:23:44', '2025-09-25 23:23:44', 1),
(71, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcyNDE1LCJqdGkiOiJmZmMwZj', '127.0.0.1', 'Desconocido', '2025-09-26 12:40:15', '2025-09-25 23:40:15', 1),
(72, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcyNDIyLCJqdGkiOiI5YTJmZm', '127.0.0.1', 'Desconocido', '2025-09-26 12:40:22', '2025-09-25 23:40:22', 1),
(73, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcyNjI5LCJqdGkiOiJkYzk4Nm', '127.0.0.1', 'Desconocido', '2025-09-26 12:43:49', '2025-09-25 23:43:49', 1),
(74, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcyNzE3LCJqdGkiOiI3YWQzND', '127.0.0.1', 'Desconocido', '2025-09-26 12:45:17', '2025-09-25 23:45:17', 1),
(75, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODcyODk5LCJqdGkiOiI3MzJmYz', '127.0.0.1', 'Desconocido', '2025-09-26 12:48:19', '2025-09-25 23:48:19', 1),
(76, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODczMDAzLCJqdGkiOiJhMGY1MG', '127.0.0.1', 'Desconocido', '2025-09-26 12:50:03', '2025-09-25 23:50:03', 1),
(77, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODczMTA2LCJqdGkiOiI3ZTk3ZD', '127.0.0.1', 'Desconocido', '2025-09-26 12:51:46', '2025-09-25 23:51:46', 1),
(78, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODczMzUxLCJqdGkiOiJiNTNhMm', '127.0.0.1', 'Desconocido', '2025-09-26 12:55:51', '2025-09-25 23:55:51', 1),
(79, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODczNTI4LCJqdGkiOiIyYWNjYz', '127.0.0.1', 'Desconocido', '2025-09-26 12:58:48', '2025-09-25 23:58:48', 1),
(80, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODczNTg0LCJqdGkiOiJlMjVhZj', '127.0.0.1', 'Desconocido', '2025-09-26 12:59:44', '2025-09-25 23:59:44', 1),
(81, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODczNjUyLCJqdGkiOiJlZTBmMW', '127.0.0.1', 'Desconocido', '2025-09-26 13:00:52', '2025-09-26 00:00:52', 1),
(82, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0MzQzLCJqdGkiOiJmZGEwNm', '127.0.0.1', 'Desconocido', '2025-09-26 13:12:23', '2025-09-26 00:12:23', 1),
(83, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0NjAwLCJqdGkiOiI3YTJkOG', '127.0.0.1', 'Desconocido', '2025-09-26 13:16:40', '2025-09-26 00:16:40', 1),
(84, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0NjIxLCJqdGkiOiJmMmJhMj', '127.0.0.1', 'Desconocido', '2025-09-26 13:17:01', '2025-09-26 00:17:01', 1),
(85, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0NjYyLCJqdGkiOiIzYTBhND', '127.0.0.1', 'Desconocido', '2025-09-26 13:17:42', '2025-09-26 00:17:42', 1),
(86, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0NjgzLCJqdGkiOiIyOWZmM2', '127.0.0.1', 'Desconocido', '2025-09-26 13:18:03', '2025-09-26 00:18:03', 1),
(87, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0ODU0LCJqdGkiOiI2MGNjNm', '127.0.0.1', 'Desconocido', '2025-09-26 13:20:54', '2025-09-26 00:20:54', 1),
(88, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0OTExLCJqdGkiOiJhZDZmOD', '127.0.0.1', 'Desconocido', '2025-09-26 13:21:51', '2025-09-26 00:21:51', 1),
(89, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc0OTM1LCJqdGkiOiI2MzQxND', '127.0.0.1', 'Desconocido', '2025-09-26 13:22:15', '2025-09-26 00:22:15', 1),
(90, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc2OTc5LCJqdGkiOiI2YjBjZD', '127.0.0.1', 'Desconocido', '2025-09-26 13:56:19', '2025-09-26 00:56:19', 1),
(91, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc3Nzg4LCJqdGkiOiI1YzkxNj', '127.0.0.1', 'Desconocido', '2025-09-26 14:09:48', '2025-09-26 01:09:48', 1),
(92, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc4MDk5LCJqdGkiOiJjN2FmZT', '127.0.0.1', 'Desconocido', '2025-09-26 14:14:59', '2025-09-26 01:14:59', 1),
(93, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc4MzQ4LCJqdGkiOiI3Y2JiZT', '127.0.0.1', 'Desconocido', '2025-09-26 14:19:08', '2025-09-26 01:19:08', 1),
(94, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc4NzQwLCJqdGkiOiI2YWExM2', '127.0.0.1', 'Desconocido', '2025-09-26 14:25:40', '2025-09-26 01:25:40', 1),
(95, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODc5MjkwLCJqdGkiOiI2MjdiNm', '127.0.0.1', 'Desconocido', '2025-09-26 14:34:50', '2025-09-26 01:34:50', 1),
(96, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODg1NjIzLCJqdGkiOiIxMmQzNT', '127.0.0.1', 'Desconocido', '2025-09-26 16:20:23', '2025-09-26 03:20:23', 1),
(97, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODg1NzI3LCJqdGkiOiJjYTkzMj', '127.0.0.1', 'Desconocido', '2025-09-26 16:22:07', '2025-09-26 03:22:07', 1),
(98, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4ODg2MzE3LCJqdGkiOiJiMGQyN2', '127.0.0.1', 'Desconocido', '2025-09-26 16:31:57', '2025-09-26 03:31:57', 1),
(99, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTMyODI1LCJqdGkiOiI5Njg2Mz', '127.0.0.1', 'Desconocido', '2025-09-27 05:27:05', '2025-09-26 16:27:05', 1),
(100, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTMyOTA1LCJqdGkiOiJkMzA1YT', '127.0.0.1', 'Desconocido', '2025-09-27 05:28:25', '2025-09-26 16:28:25', 1),
(101, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTMzMjAwLCJqdGkiOiJhNTg2ZT', '127.0.0.1', 'Desconocido', '2025-09-27 05:33:20', '2025-09-26 16:33:20', 1),
(102, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTMzNTUwLCJqdGkiOiIzZjllMT', '127.0.0.1', 'Desconocido', '2025-09-27 05:39:10', '2025-09-26 16:39:10', 1),
(103, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTMzOTQ5LCJqdGkiOiJhNjBlMD', '127.0.0.1', 'Desconocido', '2025-09-27 05:45:49', '2025-09-26 16:45:49', 1),
(104, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM0MjY1LCJqdGkiOiI3YjI0MD', '127.0.0.1', 'Desconocido', '2025-09-27 05:51:05', '2025-09-26 16:51:05', 1),
(105, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM0MzY3LCJqdGkiOiIxOTc1Zm', '127.0.0.1', 'Desconocido', '2025-09-27 05:52:47', '2025-09-26 16:52:47', 1),
(106, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM0NDcwLCJqdGkiOiI2MzNlNm', '127.0.0.1', 'Desconocido', '2025-09-27 05:54:30', '2025-09-26 16:54:30', 1),
(107, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM0NTEyLCJqdGkiOiI0NGQwNG', '127.0.0.1', 'Desconocido', '2025-09-27 05:55:12', '2025-09-26 16:55:12', 1),
(108, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM0OTcxLCJqdGkiOiI5NjA0Mz', '127.0.0.1', 'Desconocido', '2025-09-27 06:02:51', '2025-09-26 17:02:51', 1),
(109, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM1MjU4LCJqdGkiOiIxNGY5YT', '127.0.0.1', 'Desconocido', '2025-09-27 06:07:38', '2025-09-26 17:07:38', 1),
(110, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM1NTI2LCJqdGkiOiIyM2Y3Mm', '127.0.0.1', 'Desconocido', '2025-09-27 06:12:06', '2025-09-26 17:12:06', 1),
(111, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM1NjM3LCJqdGkiOiIwZWZiND', '127.0.0.1', 'Desconocido', '2025-09-27 06:13:57', '2025-09-26 17:13:57', 1),
(112, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM1NzU2LCJqdGkiOiI0NTk5ND', '127.0.0.1', 'Desconocido', '2025-09-27 06:15:56', '2025-09-26 17:15:56', 1),
(113, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM2MTc5LCJqdGkiOiI1ZmQzOT', '127.0.0.1', 'Desconocido', '2025-09-27 06:22:59', '2025-09-26 17:22:59', 1),
(114, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM2MjQyLCJqdGkiOiJiYWU4ND', '127.0.0.1', 'Desconocido', '2025-09-27 06:24:02', '2025-09-26 17:24:02', 1),
(115, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM2NDU5LCJqdGkiOiI0OWY4YT', '127.0.0.1', 'Desconocido', '2025-09-27 06:27:39', '2025-09-26 17:27:39', 1),
(116, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM3MTA0LCJqdGkiOiJhZDk1ZT', '127.0.0.1', 'Desconocido', '2025-09-27 06:38:24', '2025-09-26 17:38:24', 1),
(117, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM3MTY2LCJqdGkiOiJhNWE4Mm', '127.0.0.1', 'Desconocido', '2025-09-27 06:39:26', '2025-09-26 17:39:26', 1),
(118, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM3NTY5LCJqdGkiOiIxNTkwZW', '127.0.0.1', 'Desconocido', '2025-09-27 06:46:09', '2025-09-26 17:46:09', 1),
(119, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM3NjEzLCJqdGkiOiJjNmVhYT', '127.0.0.1', 'Desconocido', '2025-09-27 06:46:53', '2025-09-26 17:46:53', 1),
(120, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM3Nzk5LCJqdGkiOiJhMTE2ZD', '127.0.0.1', 'Desconocido', '2025-09-27 06:49:59', '2025-09-26 17:49:59', 1),
(121, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM3ODk5LCJqdGkiOiJkNDUwNG', '127.0.0.1', 'Desconocido', '2025-09-27 06:51:39', '2025-09-26 17:51:39', 1),
(122, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM4Mjc5LCJqdGkiOiJiNzYxOT', '127.0.0.1', 'Desconocido', '2025-09-27 06:57:59', '2025-09-26 17:57:59', 1),
(123, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM4MzQ4LCJqdGkiOiIxNDI0ZG', '127.0.0.1', 'Desconocido', '2025-09-27 06:59:08', '2025-09-26 17:59:08', 1),
(124, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM4NTY0LCJqdGkiOiIyYWUyYz', '127.0.0.1', 'Desconocido', '2025-09-27 07:02:44', '2025-09-26 18:02:44', 1),
(125, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTM4NjQzLCJqdGkiOiJhNzA2ZT', '127.0.0.1', 'Desconocido', '2025-09-27 07:04:03', '2025-09-26 18:04:03', 1),
(126, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTUzODQ0LCJqdGkiOiJmZmRhNm', '127.0.0.1', 'python-requests/2.28.1', '2025-09-27 11:17:24', '2025-09-26 22:17:24', 1),
(127, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTUzODU2LCJqdGkiOiJkODRiYj', '127.0.0.1', 'python-requests/2.28.1', '2025-09-27 11:17:36', '2025-09-26 22:17:36', 1),
(128, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTUzODc3LCJqdGkiOiI4OTJhZW', '127.0.0.1', 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36', '2025-09-27 11:17:57', '2025-09-26 22:17:57', 1),
(129, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOjEsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTU2MDE2LCJqdGkiOiJiMDcwY2', '127.0.0.1', 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36', '2025-09-27 11:53:36', '2025-09-26 22:53:36', 1),
(130, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY0MTcwLCJqdGkiOiJkNz', '127.0.0.1', 'Desconocido', '2025-09-27 14:09:30', '2025-09-27 01:09:30', 1),
(131, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY0MjYxLCJqdGkiOiI1Mm', '127.0.0.1', 'Desconocido', '2025-09-27 14:11:01', '2025-09-27 01:11:01', 1),
(132, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY0MzQ0LCJqdGkiOiI5M2', '127.0.0.1', 'Desconocido', '2025-09-27 14:12:24', '2025-09-27 01:12:24', 1),
(133, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY0MzcwLCJqdGkiOiI1N2', '127.0.0.1', 'Desconocido', '2025-09-27 14:12:50', '2025-09-27 01:12:50', 1),
(134, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY0NTMxLCJqdGkiOiIzYm', '127.0.0.1', 'Desconocido', '2025-09-27 14:15:31', '2025-09-27 01:15:31', 1),
(135, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY0ODc2LCJqdGkiOiIyMT', '127.0.0.1', 'Desconocido', '2025-09-27 14:21:16', '2025-09-27 01:21:16', 1),
(136, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY1NjMwLCJqdGkiOiI1NT', '127.0.0.1', 'Desconocido', '2025-09-27 14:33:50', '2025-09-27 01:33:50', 1),
(137, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY2MTQ3LCJqdGkiOiJiOW', '127.0.0.1', 'Desconocido', '2025-09-27 14:42:27', '2025-09-27 01:42:27', 1),
(138, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU4OTY2NTQ0LCJqdGkiOiIzND', '127.0.0.1', 'Desconocido', '2025-09-27 14:49:04', '2025-09-27 01:49:04', 1),
(139, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDAxMTkxLCJqdGkiOiJmZW', '127.0.0.1', 'Desconocido', '2025-09-28 00:26:31', '2025-09-27 11:26:31', 1),
(140, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI3NzI4LCJqdGkiOiIzYz', '127.0.0.1', 'Desconocido', '2025-09-28 07:48:48', '2025-09-27 18:48:48', 1),
(141, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI3ODMzLCJqdGkiOiI3ZD', '127.0.0.1', 'Desconocido', '2025-09-28 07:50:33', '2025-09-27 18:50:33', 1),
(142, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI3ODg3LCJqdGkiOiJmOT', '127.0.0.1', 'Desconocido', '2025-09-28 07:51:27', '2025-09-27 18:51:27', 1),
(143, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI3OTY4LCJqdGkiOiJkNW', '127.0.0.1', 'Desconocido', '2025-09-28 07:52:48', '2025-09-27 18:52:48', 1),
(144, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI5MzQ0LCJqdGkiOiJkMz', '127.0.0.1', 'Desconocido', '2025-09-28 08:15:44', '2025-09-27 19:15:44', 1);
INSERT INTO `UserSessions` (`id`, `user_id`, `token_id`, `ip_address`, `user_agent`, `expira`, `creado_en`, `tenant_id`) VALUES
(145, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI5NTEwLCJqdGkiOiJmZj', '127.0.0.1', 'Desconocido', '2025-09-28 08:18:30', '2025-09-27 19:18:30', 1),
(146, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI5NTcxLCJqdGkiOiJkYz', '127.0.0.1', 'Desconocido', '2025-09-28 08:19:31', '2025-09-27 19:19:31', 1),
(147, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDI5Njc0LCJqdGkiOiJhZT', '127.0.0.1', 'Desconocido', '2025-09-28 08:21:14', '2025-09-27 19:21:14', 1),
(148, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDMxMjg4LCJqdGkiOiJlMG', '127.0.0.1', 'Desconocido', '2025-09-28 08:48:08', '2025-09-27 19:48:08', 1),
(149, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDMyMDc5LCJqdGkiOiJhMG', '127.0.0.1', 'Desconocido', '2025-09-28 09:01:19', '2025-09-27 20:01:19', 1),
(150, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDMyMTA5LCJqdGkiOiJhNW', '127.0.0.1', 'Desconocido', '2025-09-28 09:01:49', '2025-09-27 20:01:49', 1),
(151, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDMyMTM1LCJqdGkiOiI5Zj', '127.0.0.1', 'Desconocido', '2025-09-28 09:02:15', '2025-09-27 20:02:15', 1),
(152, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDMzMzA4LCJqdGkiOiI5Yj', '127.0.0.1', 'Desconocido', '2025-09-28 09:21:48', '2025-09-27 20:21:48', 1),
(153, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM1Mzc3LCJqdGkiOiJiNG', '127.0.0.1', 'Desconocido', '2025-09-28 09:56:17', '2025-09-27 20:56:17', 1),
(154, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM1NDkxLCJqdGkiOiI3Nj', '127.0.0.1', 'Desconocido', '2025-09-28 09:58:11', '2025-09-27 20:58:11', 1),
(155, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM2MjIyLCJqdGkiOiIxMz', '127.0.0.1', 'Desconocido', '2025-09-28 10:10:22', '2025-09-27 21:10:22', 1),
(156, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM2NjMyLCJqdGkiOiJjND', '127.0.0.1', 'Desconocido', '2025-09-28 10:17:12', '2025-09-27 21:17:12', 1),
(157, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM3MTUxLCJqdGkiOiI2Mj', '127.0.0.1', 'Desconocido', '2025-09-28 10:25:51', '2025-09-27 21:25:51', 1),
(158, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM3NjY0LCJqdGkiOiIxND', '127.0.0.1', 'Desconocido', '2025-09-28 10:34:24', '2025-09-27 21:34:24', 1),
(159, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM4NDEzLCJqdGkiOiJiZG', '127.0.0.1', 'Desconocido', '2025-09-28 10:46:53', '2025-09-27 21:46:53', 1),
(160, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM4NzQ4LCJqdGkiOiJlOD', '127.0.0.1', 'Desconocido', '2025-09-28 10:52:28', '2025-09-27 21:52:28', 1),
(161, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM4NzU1LCJqdGkiOiJjND', '127.0.0.1', 'Desconocido', '2025-09-28 10:52:35', '2025-09-27 21:52:35', 1),
(162, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM4ODg1LCJqdGkiOiJiNT', '127.0.0.1', 'Desconocido', '2025-09-28 10:54:45', '2025-09-27 21:54:45', 1),
(163, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM5NTU1LCJqdGkiOiIzY2', '127.0.0.1', 'Desconocido', '2025-09-28 11:05:55', '2025-09-27 22:05:55', 1),
(164, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM5NjU3LCJqdGkiOiIyZj', '127.0.0.1', 'Desconocido', '2025-09-28 11:07:37', '2025-09-27 22:07:37', 1),
(165, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDM5Njg0LCJqdGkiOiJjNm', '127.0.0.1', 'Desconocido', '2025-09-28 11:08:04', '2025-09-27 22:08:04', 1),
(166, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDQwNDU0LCJqdGkiOiJmZT', '127.0.0.1', 'Desconocido', '2025-09-28 11:20:54', '2025-09-27 22:20:54', 1),
(167, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDQwNTc0LCJqdGkiOiIzOG', '127.0.0.1', 'Desconocido', '2025-09-28 11:22:54', '2025-09-27 22:22:54', 1),
(168, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnt9LCJ0ZW5hbnRfaWQiOjEsImNsaWVudGVfaWQiOm51bGwsImNsaWVudGVfbm9tYnJlIjoiRW1wcmVzYSBEZW1vIiwiZXhwIjoxNzU5MDQxNDQ0LCJqdGkiOiI5Mj', '127.0.0.1', 'Desconocido', '2025-09-28 11:37:24', '2025-09-27 22:37:24', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Vacantes`
--

CREATE TABLE `vacantes` (
  `id_vacante` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL DEFAULT 1,
  `id_cliente` int(11) NOT NULL,
  `cargo_solicitado` varchar(100) NOT NULL,
  `ciudad` varchar(50) NOT NULL,
  `requisitos` text DEFAULT NULL,
  `salario` decimal(10,2) DEFAULT NULL,
  `fecha_apertura` date DEFAULT curdate(),
  `fecha_cierre` date DEFAULT NULL,
  `estado` enum('Abierta','Cerrada','Pausada') DEFAULT 'Abierta',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Vacantes`
--

INSERT INTO `Vacantes` (`id_vacante`, `tenant_id`, `id_cliente`, `cargo_solicitado`, `ciudad`, `requisitos`, `salario`, `fecha_apertura`, `fecha_cierre`, `estado`, `created_at`) VALUES
(1, 1, 1, 'Desarrollador Frontend', 'Ciudad de México', 'React, TypeScript, 2+ años experiencia, Git, Scrum', 25000.00, '2025-09-20', NULL, 'Abierta', '2025-09-20 21:37:28'),
(2, 1, 1, 'Desarrollador Backend', 'Ciudad de México', 'Python, Flask/Django, 3+ años experiencia, APIs REST', 30000.00, '2025-09-20', NULL, 'Abierta', '2025-09-20 21:37:28'),
(3, 1, 2, 'Diseñador UX/UI', 'Guadalajara', 'Figma, Adobe Creative Suite, 2+ años experiencia, Prototipado', 22000.00, '2025-09-20', NULL, 'Abierta', '2025-09-20 21:37:28'),
(4, 1, 2, 'Product Manager', 'Guadalajara', 'Scrum, Agile, 3+ años experiencia, Análisis de datos', 35000.00, '2025-09-20', NULL, 'Abierta', '2025-09-20 21:37:28'),
(5, 1, 3, 'Marketing Digital', 'Monterrey', 'Google Ads, Facebook Ads, 2+ años experiencia, Analytics', 20000.00, '2025-09-20', NULL, 'Abierta', '2025-09-20 21:37:28'),
(6, 1, 1, 'Java DEV ', 'San Pedro Sula ', 'Experiencia como DEV ', 18000.00, '2025-09-20', NULL, 'Abierta', '2025-09-21 04:28:58'),
(7, 1, 1, 'Desarrollador Frontend', 'San Pedro Sula', 'React, JavaScript, 2 años experiencia', 25000.00, '2025-09-26', NULL, 'Abierta', '2025-09-27 01:13:02');

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_whatsapp_active_conversations`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_whatsapp_active_conversations` (
`id` int(11)
,`tenant_id` int(11)
,`conversation_id` varchar(100)
,`contact_phone` varchar(20)
,`contact_name` varchar(100)
,`last_message_at` timestamp
,`last_message_preview` text
,`unread_count` int(11)
,`status` enum('active','archived','blocked','muted')
,`is_pinned` tinyint(1)
,`priority` enum('low','normal','high','urgent')
,`tenant_name` varchar(100)
);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whatsapp_activity_logs`
--

CREATE TABLE `whatsapp_activity_logs` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `activity_type` enum('message_sent','message_received','conversation_started','conversation_ended','campaign_started','campaign_completed','connection_status','error') NOT NULL,
  `description` text DEFAULT NULL,
  `related_id` int(11) DEFAULT NULL,
  `related_type` enum('message','conversation','campaign','template') DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `user_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whatsapp_config`
--

CREATE TABLE `whatsapp_config` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `api_type` enum('business_api','whatsapp_web') NOT NULL,
  `business_api_token` varchar(500) DEFAULT NULL,
  `phone_number_id` varchar(50) DEFAULT NULL,
  `webhook_verify_token` varchar(100) DEFAULT NULL,
  `business_account_id` varchar(50) DEFAULT NULL,
  `web_session_id` varchar(100) DEFAULT NULL,
  `web_qr_code` text DEFAULT NULL,
  `web_status` enum('disconnected','qr_ready','connected','authenticated','ready') DEFAULT 'disconnected',
  `web_last_seen` timestamp NULL DEFAULT NULL,
  `webhook_url` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `auto_reconnect` tinyint(1) DEFAULT 1,
  `max_retries` int(11) DEFAULT 3,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `whatsapp_config`
--

INSERT INTO `whatsapp_config` (`id`, `tenant_id`, `api_type`, `business_api_token`, `phone_number_id`, `webhook_verify_token`, `business_account_id`, `web_session_id`, `web_qr_code`, `web_status`, `web_last_seen`, `webhook_url`, `is_active`, `auto_reconnect`, `max_retries`, `created_at`, `updated_at`) VALUES
(1, 1, 'business_api', 'EAAxxxx_example_token', '123456789012345', 'mi_token_secreto_ejemplo', '987654321098765', NULL, NULL, 'disconnected', NULL, NULL, 1, 1, 3, '2025-09-27 14:16:49', '2025-09-27 14:16:49');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whatsapp_conversations`
--

CREATE TABLE `whatsapp_conversations` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `conversation_id` varchar(100) NOT NULL,
  `contact_phone` varchar(20) NOT NULL,
  `contact_name` varchar(100) DEFAULT NULL,
  `contact_wa_id` varchar(50) DEFAULT NULL,
  `last_message_at` timestamp NULL DEFAULT NULL,
  `last_message_preview` text DEFAULT NULL,
  `unread_count` int(11) DEFAULT 0,
  `message_count` int(11) DEFAULT 0,
  `status` enum('active','archived','blocked','muted') DEFAULT 'active',
  `is_pinned` tinyint(1) DEFAULT 0,
  `priority` enum('low','normal','high','urgent') DEFAULT 'normal',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `whatsapp_conversations`
--

INSERT INTO `whatsapp_conversations` (`id`, `tenant_id`, `conversation_id`, `contact_phone`, `contact_name`, `contact_wa_id`, `last_message_at`, `last_message_preview`, `unread_count`, `message_count`, `status`, `is_pinned`, `priority`, `created_at`, `updated_at`) VALUES
(1, 1, '1_573001234567_1758983026', '573001234567', 'Juan Pérez', NULL, NULL, NULL, 0, 0, 'active', 0, 'normal', '2025-09-27 14:23:46', '2025-09-27 14:23:46');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whatsapp_messages`
--

CREATE TABLE `whatsapp_messages` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `conversation_id` int(11) NOT NULL,
  `message_id` varchar(100) NOT NULL,
  `wa_message_id` varchar(100) DEFAULT NULL,
  `direction` enum('inbound','outbound') NOT NULL,
  `message_type` enum('text','image','document','audio','video','location','contact','sticker','template') NOT NULL,
  `content` text DEFAULT NULL,
  `media_url` varchar(500) DEFAULT NULL,
  `media_mime_type` varchar(100) DEFAULT NULL,
  `media_size` int(11) DEFAULT NULL,
  `media_filename` varchar(255) DEFAULT NULL,
  `status` enum('sent','delivered','read','failed','pending') DEFAULT 'pending',
  `error_code` varchar(50) DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `wa_timestamp` timestamp NULL DEFAULT NULL,
  `context_message_id` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `whatsapp_messages`
--

INSERT INTO `whatsapp_messages` (`id`, `tenant_id`, `conversation_id`, `message_id`, `wa_message_id`, `direction`, `message_type`, `content`, `media_url`, `media_mime_type`, `media_size`, `media_filename`, `status`, `error_code`, `error_message`, `timestamp`, `wa_timestamp`, `context_message_id`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 'wamid.test123456789', 'wamid.test123456789', 'inbound', 'text', 'Hola, este es un mensaje de prueba', NULL, NULL, NULL, NULL, 'delivered', NULL, NULL, '2025-09-27 14:23:48', NULL, NULL, '2025-09-27 14:23:46', '2025-09-27 14:23:48');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Whatsapp_Templates`
--

CREATE TABLE `whatsapp_templates` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `category` enum('postulation','interview','hiring','general','marketing','reminder') NOT NULL,
  `subject` varchar(200) DEFAULT NULL,
  `content` text NOT NULL,
  `variables` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`variables`)),
  `is_active` tinyint(1) DEFAULT 1,
  `is_default` tinyint(1) DEFAULT 0,
  `usage_count` int(11) DEFAULT 0,
  `last_used_at` timestamp NULL DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `Whatsapp_Templates`
--

INSERT INTO `Whatsapp_Templates` (`id`, `tenant_id`, `name`, `category`, `subject`, `content`, `variables`, `is_active`, `is_default`, `usage_count`, `last_used_at`, `created_by`, `created_at`, `updated_at`) VALUES
(1, 1, 'Postulación Recibida', 'postulation', 'Postulación Recibida', 'Hola {{nombre}}, hemos recibido tu postulación para la vacante de {{cargo}}. Te contactaremos pronto con más información. ¡Gracias por tu interés!', NULL, 1, 1, 0, NULL, NULL, '2025-09-27 14:10:26', '2025-09-27 14:10:26'),
(2, 1, 'Entrevista Programada', 'interview', 'Entrevista Programada', 'Hola {{nombre}}, tu entrevista para {{cargo}} está programada para el {{fecha}} a las {{hora}}. Por favor confirma tu asistencia.', NULL, 1, 1, 0, NULL, NULL, '2025-09-27 14:10:26', '2025-09-27 14:10:26'),
(3, 1, 'Candidato Contratado', 'hiring', '¡Felicitaciones!', 'Hola {{nombre}}, ¡felicitaciones! Has sido seleccionado para el puesto de {{cargo}}. Te contactaremos pronto con los detalles de tu incorporación.', NULL, 1, 1, 0, NULL, NULL, '2025-09-27 14:10:26', '2025-09-27 14:10:26'),
(4, 1, 'Recordatorio de Entrevista', 'reminder', 'Recordatorio de Entrevista', 'Hola {{nombre}}, te recordamos que tienes una entrevista mañana a las {{hora}} para {{cargo}}. ¡Te esperamos!', NULL, 1, 1, 0, NULL, NULL, '2025-09-27 14:10:26', '2025-09-27 14:10:26');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whatsapp_webhooks`
--

CREATE TABLE `whatsapp_webhooks` (
  `id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `webhook_type` enum('message','status','template','account_update') NOT NULL,
  `phone_number_id` varchar(50) DEFAULT NULL,
  `raw_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`raw_data`)),
  `processed` tinyint(1) DEFAULT 0,
  `processing_error` text DEFAULT NULL,
  `received_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `processed_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_whatsapp_active_conversations`
--
DROP TABLE IF EXISTS `v_whatsapp_active_conversations`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_whatsapp_active_conversations`  AS SELECT `wc`.`id` AS `id`, `wc`.`tenant_id` AS `tenant_id`, `wc`.`conversation_id` AS `conversation_id`, `wc`.`contact_phone` AS `contact_phone`, `wc`.`contact_name` AS `contact_name`, `wc`.`last_message_at` AS `last_message_at`, `wc`.`last_message_preview` AS `last_message_preview`, `wc`.`unread_count` AS `unread_count`, `wc`.`status` AS `status`, `wc`.`is_pinned` AS `is_pinned`, `wc`.`priority` AS `priority`, `t`.`nombre_empresa` AS `tenant_name` FROM (`whatsapp_conversations` `wc` join `tenants` `t` on(`wc`.`tenant_id` = `t`.`id`)) WHERE `wc`.`status` = 'active' ORDER BY `wc`.`last_message_at` DESC ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `afiliados`
--
ALTER TABLE `afiliados`
  ADD PRIMARY KEY (`id_afiliado`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_tenant_id` (`tenant_id`),
  ADD KEY `idx_afiliados_tenant` (`tenant_id`);

--
-- Indices de la tabla `afiliado_tags`
--
ALTER TABLE `afiliado_tags`
  ADD PRIMARY KEY (`id_afiliado`,`id_tag`),
  ADD KEY `id_tag` (`id_tag`);

--
-- Indices de la tabla `calendar_reminders`
--
ALTER TABLE `calendar_reminders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_tenant_date` (`tenant_id`,`date`),
  ADD KEY `idx_tenant_type` (`tenant_id`,`type`),
  ADD KEY `idx_created_by` (`created_by`),
  ADD KEY `idx_status` (`status`);

--
-- Indices de la tabla `candidato_tags`
--
ALTER TABLE `candidato_tags`
  ADD PRIMARY KEY (`id_afiliado`,`id_tag`),
  ADD KEY `id_tag` (`id_tag`);

--
-- Indices de la tabla `clientes`
--
ALTER TABLE `clientes`
  ADD PRIMARY KEY (`id_cliente`),
  ADD KEY `idx_clientes_tenant_id` (`tenant_id`);

--
-- Indices de la tabla `contratados`
--
ALTER TABLE `contratados`
  ADD PRIMARY KEY (`id_contratado`),
  ADD KEY `id_afiliado` (`id_afiliado`),
  ADD KEY `id_vacante` (`id_vacante`);

--
-- Indices de la tabla `documentos`
--
ALTER TABLE `documentos`
  ADD PRIMARY KEY (`id_documento`),
  ADD KEY `idx_afiliado` (`id_afiliado`);

--
-- Indices de la tabla `email_templates`
--
ALTER TABLE `email_templates`
  ADD PRIMARY KEY (`id_template`),
  ADD KEY `id_cliente` (`id_cliente`),
  ADD KEY `idx_email_templates_tenant` (`tenant_id`);

--
-- Indices de la tabla `entrevistas`
--
ALTER TABLE `entrevistas`
  ADD PRIMARY KEY (`id_entrevista`),
  ADD KEY `id_postulacion` (`id_postulacion`);

--
-- Indices de la tabla `errorlogs`
--
ALTER TABLE `errorlogs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `interviews`
--
ALTER TABLE `interviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_tenant_date` (`tenant_id`,`interview_date`),
  ADD KEY `idx_candidate` (`candidate_id`),
  ADD KEY `idx_vacancy` (`vacancy_id`),
  ADD KEY `idx_status` (`status`);

--
-- Indices de la tabla `mensajes_contacto`
--
ALTER TABLE `mensajes_contacto`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `posts`
--
ALTER TABLE `posts`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `postulaciones`
--
ALTER TABLE `postulaciones`
  ADD PRIMARY KEY (`id_postulacion`),
  ADD KEY `id_afiliado` (`id_afiliado`),
  ADD KEY `id_vacante` (`id_vacante`),
  ADD KEY `idx_postulaciones_tenant_id` (`tenant_id`),
  ADD KEY `idx_postulaciones_tenant` (`tenant_id`);

--
-- Indices de la tabla `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `tags`
--
ALTER TABLE `tags`
  ADD PRIMARY KEY (`id_tag`),
  ADD KEY `id_cliente` (`id_cliente`),
  ADD KEY `idx_tags_tenant` (`tenant_id`);

--
-- Indices de la tabla `tenants`
--
ALTER TABLE `tenants`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `useractivitylog`
--
ALTER TABLE `useractivitylog`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `rol_id` (`rol_id`),
  ADD KEY `idx_users_tenant_id` (`tenant_id`),
  ADD KEY `idx_users_tenant` (`tenant_id`);

--
-- Indices de la tabla `usersessions`
--
ALTER TABLE `usersessions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_token_id` (`token_id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_expira` (`expira`);

--
-- Indices de la tabla `vacantes`
--
ALTER TABLE `vacantes`
  ADD PRIMARY KEY (`id_vacante`),
  ADD KEY `id_cliente` (`id_cliente`),
  ADD KEY `idx_vacantes_tenant_id` (`tenant_id`),
  ADD KEY `idx_vacantes_tenant` (`tenant_id`);

--
-- Indices de la tabla `whatsapp_activity_logs`
--
ALTER TABLE `whatsapp_activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_tenant_activity` (`tenant_id`,`activity_type`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_related` (`related_type`,`related_id`);

--
-- Indices de la tabla `whatsapp_config`
--
ALTER TABLE `whatsapp_config`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_tenant_api` (`tenant_id`,`api_type`),
  ADD KEY `idx_tenant_active` (`tenant_id`,`is_active`),
  ADD KEY `idx_phone_number` (`phone_number_id`),
  ADD KEY `idx_web_session` (`web_session_id`);

--
-- Indices de la tabla `whatsapp_conversations`
--
ALTER TABLE `whatsapp_conversations`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_conversation` (`tenant_id`,`conversation_id`),
  ADD KEY `idx_tenant_phone` (`tenant_id`,`contact_phone`),
  ADD KEY `idx_tenant_status` (`tenant_id`,`status`),
  ADD KEY `idx_last_message` (`last_message_at`),
  ADD KEY `idx_unread` (`tenant_id`,`unread_count`);

--
-- Indices de la tabla `whatsapp_messages`
--
ALTER TABLE `whatsapp_messages`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_message` (`tenant_id`,`message_id`),
  ADD KEY `idx_conversation_timestamp` (`conversation_id`,`timestamp`),
  ADD KEY `idx_tenant_timestamp` (`tenant_id`,`timestamp`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_message_type` (`message_type`),
  ADD KEY `idx_direction` (`direction`);

--
-- Indices de la tabla `whatsapp_templates`
--
ALTER TABLE `whatsapp_templates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `idx_tenant_category` (`tenant_id`,`category`),
  ADD KEY `idx_tenant_active` (`tenant_id`,`is_active`),
  ADD KEY `idx_usage_count` (`usage_count`);

--
-- Indices de la tabla `whatsapp_webhooks`
--
ALTER TABLE `whatsapp_webhooks`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_tenant_type` (`tenant_id`,`webhook_type`),
  ADD KEY `idx_processed` (`processed`),
  ADD KEY `idx_received_at` (`received_at`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `afiliados`
--
ALTER TABLE `afiliados`
  MODIFY `id_afiliado` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT de la tabla `calendar_reminders`
--
ALTER TABLE `calendar_reminders`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `clientes`
--
ALTER TABLE `clientes`
  MODIFY `id_cliente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `contratados`
--
ALTER TABLE `contratados`
  MODIFY `id_contratado` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `documentos`
--
ALTER TABLE `documentos`
  MODIFY `id_documento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `email_templates`
--
ALTER TABLE `email_templates`
  MODIFY `id_template` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `entrevistas`
--
ALTER TABLE `entrevistas`
  MODIFY `id_entrevista` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `errorlogs`
--
ALTER TABLE `errorlogs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `interviews`
--
ALTER TABLE `interviews`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `mensajes_contacto`
--
ALTER TABLE `mensajes_contacto`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `posts`
--
ALTER TABLE `posts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `postulaciones`
--
ALTER TABLE `postulaciones`
  MODIFY `id_postulacion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `tags`
--
ALTER TABLE `tags`
  MODIFY `id_tag` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `tenants`
--
ALTER TABLE `tenants`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `useractivitylog`
--
ALTER TABLE `useractivitylog`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=174;

--
-- AUTO_INCREMENT de la tabla `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `usersessions`
--
ALTER TABLE `usersessions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=169;

--
-- AUTO_INCREMENT de la tabla `vacantes`
--
ALTER TABLE `vacantes`
  MODIFY `id_vacante` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `whatsapp_activity_logs`
--
ALTER TABLE `whatsapp_activity_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `whatsapp_config`
--
ALTER TABLE `whatsapp_config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `whatsapp_conversations`
--
ALTER TABLE `whatsapp_conversations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `whatsapp_messages`
--
ALTER TABLE `whatsapp_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `whatsapp_templates`
--
ALTER TABLE `whatsapp_templates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `whatsapp_webhooks`
--
ALTER TABLE `whatsapp_webhooks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `afiliado_tags`
--
ALTER TABLE `afiliado_tags`
  ADD CONSTRAINT `afiliado_tags_ibfk_1` FOREIGN KEY (`id_afiliado`) REFERENCES `Afiliados` (`id_afiliado`) ON DELETE CASCADE,
  ADD CONSTRAINT `afiliado_tags_ibfk_2` FOREIGN KEY (`id_tag`) REFERENCES `Tags` (`id_tag`) ON DELETE CASCADE;

--
-- Filtros para la tabla `candidato_tags`
--
ALTER TABLE `candidato_tags`
  ADD CONSTRAINT `candidato_tags_ibfk_1` FOREIGN KEY (`id_afiliado`) REFERENCES `Afiliados` (`id_afiliado`),
  ADD CONSTRAINT `candidato_tags_ibfk_2` FOREIGN KEY (`id_tag`) REFERENCES `Tags` (`id_tag`);

--
-- Filtros para la tabla `contratados`
--
ALTER TABLE `contratados`
  ADD CONSTRAINT `contratados_ibfk_1` FOREIGN KEY (`id_afiliado`) REFERENCES `Afiliados` (`id_afiliado`),
  ADD CONSTRAINT `contratados_ibfk_2` FOREIGN KEY (`id_vacante`) REFERENCES `Vacantes` (`id_vacante`);

--
-- Filtros para la tabla `documentos`
--
ALTER TABLE `documentos`
  ADD CONSTRAINT `documentos_ibfk_1` FOREIGN KEY (`id_afiliado`) REFERENCES `Afiliados` (`id_afiliado`) ON DELETE CASCADE;

--
-- Filtros para la tabla `email_templates`
--
ALTER TABLE `email_templates`
  ADD CONSTRAINT `email_templates_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `Clientes` (`id_cliente`);

--
-- Filtros para la tabla `entrevistas`
--
ALTER TABLE `entrevistas`
  ADD CONSTRAINT `entrevistas_ibfk_1` FOREIGN KEY (`id_postulacion`) REFERENCES `Postulaciones` (`id_postulacion`);

--
-- Filtros para la tabla `errorlogs`
--
ALTER TABLE `errorlogs`
  ADD CONSTRAINT `errorlogs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `postulaciones`
--
ALTER TABLE `postulaciones`
  ADD CONSTRAINT `postulaciones_ibfk_1` FOREIGN KEY (`id_afiliado`) REFERENCES `Afiliados` (`id_afiliado`),
  ADD CONSTRAINT `postulaciones_ibfk_2` FOREIGN KEY (`id_vacante`) REFERENCES `Vacantes` (`id_vacante`);

--
-- Filtros para la tabla `tags`
--
ALTER TABLE `tags`
  ADD CONSTRAINT `tags_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `Clientes` (`id_cliente`);

--
-- Filtros para la tabla `useractivitylog`
--
ALTER TABLE `useractivitylog`
  ADD CONSTRAINT `useractivitylog_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`rol_id`) REFERENCES `Roles` (`id`);

--
-- Filtros para la tabla `usersessions`
--
ALTER TABLE `usersessions`
  ADD CONSTRAINT `usersessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `vacantes`
--
ALTER TABLE `vacantes`
  ADD CONSTRAINT `vacantes_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `Clientes` (`id_cliente`);

--
-- Filtros para la tabla `whatsapp_activity_logs`
--
ALTER TABLE `whatsapp_activity_logs`
  ADD CONSTRAINT `whatsapp_activity_logs_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `whatsapp_activity_logs_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `whatsapp_config`
--
ALTER TABLE `whatsapp_config`
  ADD CONSTRAINT `whatsapp_config_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `whatsapp_conversations`
--
ALTER TABLE `whatsapp_conversations`
  ADD CONSTRAINT `whatsapp_conversations_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `whatsapp_messages`
--
ALTER TABLE `whatsapp_messages`
  ADD CONSTRAINT `whatsapp_messages_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `whatsapp_messages_ibfk_2` FOREIGN KEY (`conversation_id`) REFERENCES `whatsapp_conversations` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `whatsapp_templates`
--
ALTER TABLE `whatsapp_templates`
  ADD CONSTRAINT `whatsapp_templates_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `whatsapp_templates_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `Users` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `whatsapp_webhooks`
--
ALTER TABLE `whatsapp_webhooks`
  ADD CONSTRAINT `whatsapp_webhooks_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `Tenants` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
