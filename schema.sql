CREATE TABLE IF NOT EXISTS pacientes (
    id VARCHAR(255) PRIMARY KEY,
    nombre VARCHAR(255),
    apellido VARCHAR(255),
    genero VARCHAR(50),
    fecha_nacimiento DATE,
    fuente_json JSONB
);

CREATE TABLE IF NOT EXISTS encuentros (
    id VARCHAR(255) PRIMARY KEY,
    id_paciente VARCHAR(255) REFERENCES pacientes(id),
    fecha TIMESTAMP,
    tipo VARCHAR(255),
    motivo TEXT,
    fuente_json JSONB
);

CREATE TABLE IF NOT EXISTS condiciones (
    id VARCHAR(255) PRIMARY KEY,
    id_paciente VARCHAR(255) REFERENCES pacientes(id),
    descripcion TEXT,
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    fuente_json JSONB
);

CREATE TABLE IF NOT EXISTS observaciones (
    id VARCHAR(255) PRIMARY KEY,
    id_paciente VARCHAR(255) REFERENCES pacientes(id),
    id_encuentro VARCHAR(255) REFERENCES encuentros(id),
    codigo VARCHAR(100),
    descripcion TEXT,
    valor VARCHAR(255),
    unidad VARCHAR(50),
    fecha TIMESTAMP,
    fuente_json JSONB
);

CREATE TABLE IF NOT EXISTS medicamentos (
    id VARCHAR(255) PRIMARY KEY,
    id_paciente VARCHAR(255) REFERENCES pacientes(id),
    id_encuentro VARCHAR(255) REFERENCES encuentros(id),
    nombre_medicamento VARCHAR(255),
    fecha_inicio TIMESTAMP,
    estado VARCHAR(50),
    fuente_json JSONB
);