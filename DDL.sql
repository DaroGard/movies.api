CREATE SCHEMA cinema AUTHORIZATION dbo;

CREATE TABLE cinema.movies (
  movieId INT IDENTITY(1,1) PRIMARY KEY,
  title NVARCHAR(255) NOT NULL,
  genres NVARCHAR(255) NULL
);

CREATE TABLE cinema.users (
    uid VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    is_admin BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

CREATE PROCEDURE cinema.users_insert
    @uid VARCHAR(50),
    @email VARCHAR(255),
    @is_admin BIT,
    @is_active BIT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM cinema.users WHERE uid = @uid OR email = @email)
    BEGIN
        RAISERROR('El usuario ya existe.', 16, 1);
        RETURN;
    END

    INSERT INTO cinema.users (uid, email, is_admin, is_active)
    VALUES (@uid, @email, @is_admin, @is_active);
END;