-- ==============================================================================
-- PROYECTO CIMSI - DATOS INICIALES (SEED DATA)
-- Cuentas de prueba para el equipo y pruebas iniciales
-- Contraseña por defecto para todas las cuentas: 'cimsi2627'
-- ==============================================================================

-- Hash bcrypt precalculado para la contraseña 'cimsi2627'
INSERT INTO players (id, username, password_hash, email) VALUES
(1, 'admin',   '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'admin@cimsi.etsii.es'),
(2, 'player1', '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'player1@cimsi.etsii.es'),
(3, 'raul',    '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'raul@cimsi.etsii.es'),
(4, 'santi',   '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'santi@cimsi.etsii.es'),
(5, 'jose',    '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'jose@cimsi.etsii.es'),
(6, 'david',   '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'david@cimsi.etsii.es'),
(7, 'pablo',   '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'pablo@cimsi.etsii.es'),
(8, 'alfonso', '$2a$12$WbMzKL1rBJ1u74BRTzUy7ul6h5II/gs/1JZSVlNYrb0ln5Ntl595C', 'alfonso@cimsi.etsii.es')
ON CONFLICT (id) DO NOTHING;

-- Sincronizar la secuencia de autoincremento con el ID máximo insertado
SELECT setval('players_id_seq', (SELECT MAX(id) FROM players));
