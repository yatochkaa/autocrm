--
-- PostgreSQL database dump
--

\restrict 4hD9iUxHfj7zdXcfgnCccY1j8nas5IaiayFfeh3lKmjiRaNDoXpMd4qlrYlq4I5

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: partsprice
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO partsprice;

--
-- Name: comments; Type: TABLE; Schema: public; Owner: partsprice
--

CREATE TABLE public.comments (
    id integer NOT NULL,
    lead_id integer NOT NULL,
    author_id integer,
    text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.comments OWNER TO partsprice;

--
-- Name: comments_id_seq; Type: SEQUENCE; Schema: public; Owner: partsprice
--

CREATE SEQUENCE public.comments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.comments_id_seq OWNER TO partsprice;

--
-- Name: comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: partsprice
--

ALTER SEQUENCE public.comments_id_seq OWNED BY public.comments.id;


--
-- Name: leads; Type: TABLE; Schema: public; Owner: partsprice
--

CREATE TABLE public.leads (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    phone character varying(50),
    source character varying(20) DEFAULT 'manual'::character varying NOT NULL,
    vin character varying(17),
    car_info character varying(255),
    status character varying(20) DEFAULT 'new'::character varying NOT NULL,
    manager_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.leads OWNER TO partsprice;

--
-- Name: leads_id_seq; Type: SEQUENCE; Schema: public; Owner: partsprice
--

CREATE SEQUENCE public.leads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.leads_id_seq OWNER TO partsprice;

--
-- Name: leads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: partsprice
--

ALTER SEQUENCE public.leads_id_seq OWNED BY public.leads.id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: partsprice
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    lead_id integer NOT NULL,
    oem character varying(100),
    brand character varying(100),
    name character varying(255) NOT NULL,
    price numeric(12,2),
    qty integer DEFAULT 1 NOT NULL,
    is_analog boolean DEFAULT false NOT NULL,
    purchase_price numeric(12,2)
);


ALTER TABLE public.order_items OWNER TO partsprice;

--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: partsprice
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.order_items_id_seq OWNER TO partsprice;

--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: partsprice
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: status_history; Type: TABLE; Schema: public; Owner: partsprice
--

CREATE TABLE public.status_history (
    id integer NOT NULL,
    lead_id integer NOT NULL,
    from_status character varying(30),
    to_status character varying(30) NOT NULL,
    changed_by integer,
    changed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.status_history OWNER TO partsprice;

--
-- Name: status_history_id_seq; Type: SEQUENCE; Schema: public; Owner: partsprice
--

CREATE SEQUENCE public.status_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.status_history_id_seq OWNER TO partsprice;

--
-- Name: status_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: partsprice
--

ALTER SEQUENCE public.status_history_id_seq OWNED BY public.status_history.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: partsprice
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) DEFAULT 'manager'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO partsprice;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: partsprice
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO partsprice;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: partsprice
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: comments id; Type: DEFAULT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.comments ALTER COLUMN id SET DEFAULT nextval('public.comments_id_seq'::regclass);


--
-- Name: leads id; Type: DEFAULT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.leads ALTER COLUMN id SET DEFAULT nextval('public.leads_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: status_history id; Type: DEFAULT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.status_history ALTER COLUMN id SET DEFAULT nextval('public.status_history_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: partsprice
--

COPY public.alembic_version (version_num) FROM stdin;
0002
\.


--
-- Data for Name: comments; Type: TABLE DATA; Schema: public; Owner: partsprice
--

COPY public.comments (id, lead_id, author_id, text, created_at) FROM stdin;
\.


--
-- Data for Name: leads; Type: TABLE DATA; Schema: public; Owner: partsprice
--

COPY public.leads (id, name, phone, source, vin, car_info, status, manager_id, created_at, updated_at) FROM stdin;
1	Алексей Морозов	+79990001001	telegram	XTA210990Y2765432	Lada Vesta 2020	new	2	2026-07-17 04:16:38.458072+00	2026-07-17 08:16:38.458072+00
2	Марина Крылова	+79990001002	site	Z94CB41AAGR323456	Kia Rio 2017	new	2	2026-07-16 04:16:38.464016+00	2026-07-16 08:16:38.464016+00
3	Дмитрий Соколов	+79990001003	manual	Z94K241CBLR123456	Hyundai Solaris 2020	new	2	2026-07-15 04:16:38.471696+00	2026-07-15 08:16:38.471696+00
4	Ольга Белова	+79990001004	telegram	XW7BF4FK90S123456	Toyota Camry 2019	in_progress	2	2026-07-14 04:16:38.478732+00	2026-07-14 08:16:38.478732+00
5	Сергей Павлов	+79990001005	site	XW8ZZZ61ZKG123456	Volkswagen Polo 2019	in_progress	2	2026-07-13 04:16:38.483112+00	2026-07-13 08:16:38.483112+00
6	Анна Волкова	+79990001006	manual	X7LLSRB1H5H123456	Renault Logan 2017	in_progress	2	2026-07-12 04:16:38.493472+00	2026-07-12 08:16:38.493472+00
7	Иван Кузнецов	+79990001007	telegram	TMBJG7NE7H0123456	Skoda Octavia 2017	selection	2	2026-07-11 04:16:38.49985+00	2026-07-11 08:16:38.49985+00
8	Елена Фролова	+79990001008	site	X9F4XXEED4AB12345	Ford Focus 2014	selection	2	2026-07-10 04:16:38.50483+00	2026-07-10 08:16:38.50483+00
9	Николай Власов	+79990001009	manual	XTA219010K0123456	Lada Granta 2019	selection	2	2026-07-09 04:16:38.516367+00	2026-07-09 08:16:38.516367+00
10	Татьяна Орлова	+79990001010	telegram	Z94C251CBJR123456	Hyundai Creta 2018	invoice	2	2026-07-08 04:16:38.524534+00	2026-07-08 08:16:38.524534+00
11	Михаил Данилов	+79990001011	site	XW8AN2NE9LH123456	Skoda Octavia 2020	invoice	2	2026-07-07 04:16:38.531793+00	2026-07-07 08:16:38.531793+00
12	Виктория Лебедева	+79990001012	manual	X7M4SRAV50K123456	Renault Duster 2019	invoice	2	2026-07-06 04:16:38.540342+00	2026-07-06 08:16:38.540342+00
13	Андрей Егоров	+79990001013	telegram	XW7BK4FK30S123456	Toyota Camry 2021	won	2	2026-07-03 04:16:38.547737+00	2026-07-03 08:16:38.547737+00
14	Светлана Романова	+79990001014	site	XW8ZZZ61ZJG123456	Volkswagen Polo 2018	won	2	2026-06-29 04:16:38.555259+00	2026-06-29 08:16:38.555259+00
15	Павел Никитин	+79990001015	manual	XTA217230J0123456	Lada Priora 2018	lost	2	2026-06-27 04:16:38.563351+00	2026-06-27 08:16:38.563351+00
16	Ирина Семёнова	+79990001016	telegram	Z94CB41AAHR123456	Kia Rio 2017	lost	2	2026-06-23 04:16:38.570667+00	2026-06-23 08:16:38.570667+00
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: partsprice
--

COPY public.order_items (id, lead_id, oem, brand, name, price, qty, is_analog, purchase_price) FROM stdin;
1	1	21080-1012005	LADA	Фильтр масляный	650.00	2	f	410.00
2	2	58101-H5A25	Mando	Колодки передние	5400.00	1	f	3900.00
3	4	48820-33070	Toyota	Стойка стабилизатора	4300.00	2	f	3100.00
4	5	04E905612C	NGK	Свеча зажигания	1450.00	4	t	920.00
5	7	04E198119	INA	Комплект ГРМ	18900.00	1	t	13900.00
6	7	04E121600	HEPU	Помпа	8200.00	1	t	6100.00
7	8	1709762	Sachs	Амортизатор передний	9800.00	2	t	7200.00
8	9	21120-3501070	LADA	Диск тормозной	3600.00	2	f	2450.00
9	9	11180-3501080	Trialli	Колодки передние	2100.00	1	t	1350.00
10	10	92101-M0000	Hyundai	Фара левая	38500.00	1	f	29800.00
11	11	5Q0121251GN	Nissens	Радиатор охлаждения	24700.00	1	t	18400.00
12	11	G12E050A2	VAG	Антифриз 5 л	3200.00	2	f	2250.00
13	12	302055852R	Valeo	Сцепление комплект	22800.00	1	t	16900.00
14	13	52119-33B30	Toyota	Бампер передний	52000.00	1	f	40500.00
15	13	52535-33040	Toyota	Крепление бампера	1800.00	2	f	1100.00
16	14	6R0820803R	Denso	Компрессор кондиционера	46500.00	1	t	35200.00
17	15	21700-3701010	КЗАТЭ	Генератор	15400.00	1	f	12100.00
18	16	76004-H0000	Kia	Дверь передняя правая	67000.00	1	f	52000.00
\.


--
-- Data for Name: status_history; Type: TABLE DATA; Schema: public; Owner: partsprice
--

COPY public.status_history (id, lead_id, from_status, to_status, changed_by, changed_at) FROM stdin;
1	4	new	in_progress	2	2026-07-14 05:16:38.478732+00
2	5	new	in_progress	2	2026-07-13 05:16:38.483112+00
3	6	new	in_progress	2	2026-07-12 05:16:38.493472+00
4	7	new	in_progress	2	2026-07-11 05:16:38.49985+00
5	7	in_progress	selection	2	2026-07-11 06:16:38.49985+00
6	8	new	in_progress	2	2026-07-10 05:16:38.50483+00
7	8	in_progress	selection	2	2026-07-10 06:16:38.50483+00
8	9	new	in_progress	2	2026-07-09 05:16:38.516367+00
9	9	in_progress	selection	2	2026-07-09 06:16:38.516367+00
10	10	new	in_progress	2	2026-07-08 05:16:38.524534+00
11	10	in_progress	selection	2	2026-07-08 06:16:38.524534+00
12	10	selection	invoice	2	2026-07-08 07:16:38.524534+00
13	11	new	in_progress	2	2026-07-07 05:16:38.531793+00
14	11	in_progress	selection	2	2026-07-07 06:16:38.531793+00
15	11	selection	invoice	2	2026-07-07 07:16:38.531793+00
16	12	new	in_progress	2	2026-07-06 05:16:38.540342+00
17	12	in_progress	selection	2	2026-07-06 06:16:38.540342+00
18	12	selection	invoice	2	2026-07-06 07:16:38.540342+00
19	13	new	in_progress	2	2026-07-03 05:16:38.547737+00
20	13	in_progress	selection	2	2026-07-03 06:16:38.547737+00
21	13	selection	invoice	2	2026-07-03 07:16:38.547737+00
22	13	invoice	won	2	2026-07-03 08:16:38.547737+00
23	14	new	in_progress	2	2026-06-29 05:16:38.555259+00
24	14	in_progress	selection	2	2026-06-29 06:16:38.555259+00
25	14	selection	invoice	2	2026-06-29 07:16:38.555259+00
26	14	invoice	won	2	2026-06-29 08:16:38.555259+00
27	15	new	in_progress	2	2026-06-27 05:16:38.563351+00
28	15	in_progress	selection	2	2026-06-27 06:16:38.563351+00
29	15	selection	invoice	2	2026-06-27 07:16:38.563351+00
30	15	invoice	lost	2	2026-06-27 08:16:38.563351+00
31	16	new	in_progress	2	2026-06-23 05:16:38.570667+00
32	16	in_progress	selection	2	2026-06-23 06:16:38.570667+00
33	16	selection	invoice	2	2026-06-23 07:16:38.570667+00
34	16	invoice	lost	2	2026-06-23 08:16:38.570667+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: partsprice
--

COPY public.users (id, email, password_hash, role, created_at) FROM stdin;
1	volgarec999@mail.ru	$2b$12$SHR3P9ONX4mND53ac80nmebSb9vzsQ8tF8RVW9vlCwPHHsQxWMOz2	admin	2026-07-17 04:16:37.995445+00
2	manager@autocrm.local	$2b$12$fvr/GqR0oxcd9KVedvccD.dANZzHK5ZTYTVOeBbMJLnNeh87v4dSm	manager	2026-07-17 04:16:37.995445+00
\.


--
-- Name: comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: partsprice
--

SELECT pg_catalog.setval('public.comments_id_seq', 1, false);


--
-- Name: leads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: partsprice
--

SELECT pg_catalog.setval('public.leads_id_seq', 16, true);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: partsprice
--

SELECT pg_catalog.setval('public.order_items_id_seq', 18, true);


--
-- Name: status_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: partsprice
--

SELECT pg_catalog.setval('public.status_history_id_seq', 34, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: partsprice
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: comments pk_comments; Type: CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT pk_comments PRIMARY KEY (id);


--
-- Name: leads pk_leads; Type: CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT pk_leads PRIMARY KEY (id);


--
-- Name: order_items pk_order_items; Type: CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT pk_order_items PRIMARY KEY (id);


--
-- Name: status_history pk_status_history; Type: CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.status_history
    ADD CONSTRAINT pk_status_history PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT pk_users PRIMARY KEY (id);


--
-- Name: ix_comments_author_id; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_comments_author_id ON public.comments USING btree (author_id);


--
-- Name: ix_comments_lead_id; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_comments_lead_id ON public.comments USING btree (lead_id);


--
-- Name: ix_leads_manager_id; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_leads_manager_id ON public.leads USING btree (manager_id);


--
-- Name: ix_leads_phone; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_leads_phone ON public.leads USING btree (phone);


--
-- Name: ix_leads_status; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_leads_status ON public.leads USING btree (status);


--
-- Name: ix_leads_vin; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_leads_vin ON public.leads USING btree (vin);


--
-- Name: ix_order_items_lead_id; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_order_items_lead_id ON public.order_items USING btree (lead_id);


--
-- Name: ix_order_items_oem; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_order_items_oem ON public.order_items USING btree (oem);


--
-- Name: ix_status_history_changed_by; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_status_history_changed_by ON public.status_history USING btree (changed_by);


--
-- Name: ix_status_history_lead_id; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE INDEX ix_status_history_lead_id ON public.status_history USING btree (lead_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: partsprice
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: comments fk_comments_author_id_users; Type: FK CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT fk_comments_author_id_users FOREIGN KEY (author_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: comments fk_comments_lead_id_leads; Type: FK CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT fk_comments_lead_id_leads FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- Name: leads fk_leads_manager_id_users; Type: FK CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT fk_leads_manager_id_users FOREIGN KEY (manager_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: order_items fk_order_items_lead_id_leads; Type: FK CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_items_lead_id_leads FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- Name: status_history fk_status_history_changed_by_users; Type: FK CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.status_history
    ADD CONSTRAINT fk_status_history_changed_by_users FOREIGN KEY (changed_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: status_history fk_status_history_lead_id_leads; Type: FK CONSTRAINT; Schema: public; Owner: partsprice
--

ALTER TABLE ONLY public.status_history
    ADD CONSTRAINT fk_status_history_lead_id_leads FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 4hD9iUxHfj7zdXcfgnCccY1j8nas5IaiayFfeh3lKmjiRaNDoXpMd4qlrYlq4I5

