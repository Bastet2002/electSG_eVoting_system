
drop table if exists SingPass_User;
drop table if exists Voter;
drop table if exists Voter_secretkey;
drop table if exists Candidate_publickey;
drop table if exists Candidate_secretkey;
drop table if exists Vote_records;
drop table if exists Vote_results;

-- can have district_id for simplicity
CREATE TABLE Singpass_User (
    id VARCHAR(9) PRIMARY KEY,
    district VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    DOB DATE NOT NULL
);

CREATE TABLE Voter (
    voter_id SERIAL PRIMARY KEY,
    district_id BIGINT NOT NULL,
    hashfrominfo VARCHAR(64) UNIQUE, -- A 512bit hash, with H(disctrict_id, id, name, phone, DOB)
    pkV VARCHAR(32) NOT NULL,
    FOREIGN KEY (district_id) REFERENCES myapp_district(id) -- no delete cascade
);

CREATE TABLE Voter_SecretKey (
    pkV VARCHAR(32) PRIMARY KEY,
    skV VARCHAR(32) NOT NULL UNIQUE,
    pkS VARCHAR(32) NOT NULL UNIQUE,
    skS VARCHAR(32) NOT NULL UNIQUE
);

CREATE TABLE Candidate_PublicKey (
    candidate_id BIGINT PRIMARY KEY,
    pkV VARCHAR(32) NOT NULL UNIQUE,
    pkS VARCHAR(32) NOT NULL UNIQUE,
    FOREIGN KEY (candidate_id) REFERENCES myapp_useraccount(id) ON DELETE CASCADE
);

CREATE TABLE Candidate_SecretKey (
    pkV VARCHAR(32) PRIMARY KEY,
    skV VARCHAR(32) NOT NULL UNIQUE,
    pkS VARCHAR(32) NOT NULL UNIQUE,
    skS VARCHAR(32) NOT NULL UNIQUE
);

CREATE TABLE Vote_Records (
    key_image VARCHAR(32) PRIMARY KEY,
    district_id BIGINT NOT NULL,
    transaction_record JSONB NOT NULL, 
    FOREIGN KEY (district_id) REFERENCES myapp_district(id) -- no delete cascade
);

CREATE TABLE Vote_Results (
    district_id BIGINT NOT NULL,
    candidate_id BIGINT NOT NULL,
    total_vote INTEGER NOT NULL,
    PRIMARY KEY (district_id, candidate_id),
    FOREIGN KEY (candidate_id) REFERENCES myapp_useraccount(id), -- no delete cascade
    FOREIGN KEY (district_id) REFERENCES myapp_district(id) -- no delete cascade
);