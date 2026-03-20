BEGIN;

CREATE SCHEMA guilds;
CREATE EXTENSION hstore WITH SCHEMA guilds CASCADE;
SET search_path TO guilds;

CREATE TABLE IF NOT EXISTS guilds
(
    id integer NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS users
(
    id integer NOT NULL,
    guild_id integer,
    colour integer[],
    shutup boolean,
    points integer,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS levels_keys
(
    id integer NOT NULL,
    levelup_message character varying(250),
    levelup_message_dm character varying(250),
    roleup_message character varying(250),
    roleup_message_dm character varying(250),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS levels_config
(
    id integer NOT NULL,
    base integer DEFAULT 50,
    growth_rate real DEFAULT 1.2,
    points_range int4range DEFAULT '[1,5]',
    message_cooldown integer DEFAULT 30,
    alert_channel integer,
    levels hstore,
    colour integer[],
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS disabled_channels
(
    id integer NOT NULL,
    guild_id integer,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS welcome_config
(
    id integer NOT NULL,
    notifchannel integer,
    joinmsg character varying(1000) DEFAULT 'welcome, {mention}!',
    welcomemsg character varying(1000) DEFAULT '{username} left the server :(',
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS users
    ADD FOREIGN KEY (guild_id)
    REFERENCES guilds (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT
    NOT VALID;


ALTER TABLE IF EXISTS levels_keys
    ADD FOREIGN KEY (id)
    REFERENCES levels_config (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT
    NOT VALID;


ALTER TABLE IF EXISTS levels_config
    ADD FOREIGN KEY (id)
    REFERENCES guilds (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT
    NOT VALID;


ALTER TABLE IF EXISTS disabled_channels
    ADD FOREIGN KEY (guild_id)
    REFERENCES levels_config (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT
    NOT VALID;


ALTER TABLE IF EXISTS welcome_config
    ADD FOREIGN KEY (id)
    REFERENCES guilds (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT
    NOT VALID;

END;