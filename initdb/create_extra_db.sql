DO
$$
BEGIN
    -- Eğer staging veritabanı varsa, sil
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'staging') THEN
        DROP DATABASE staging;
    END IF;

    -- Veritabanını yeniden oluştur
    CREATE DATABASE staging;

    -- Veritabanı yetkilerini ayarla
    GRANT ALL PRIVILEGES ON DATABASE staging TO postgres;
END
$$;