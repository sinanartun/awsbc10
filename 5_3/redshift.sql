CREATE TABLE "public"."btcusdt"(id         bigint NOT NULL,
                                 symbol     character(7) NOT NULL encode lzo,
                                 price      numeric(7,2) encode delta32k,
                                 quantity   numeric(7,5) encode delta32k,
                                 trade_time timestamp without time zone encode az64,
                                 maker      boolean,
                                 CONSTRAINT id_pkey2 PRIMARY KEY(id)) distkey(id) compound sortkey(id,trade_time);