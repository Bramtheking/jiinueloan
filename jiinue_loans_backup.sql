--
-- PostgreSQL database dump
--

\restrict vUSxP2qYM0kgFA49dbf9UB8Cod7CfPXrzGVsY1YA7f2ftRz0FIar9KQbAV0IlGe

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: deposittype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.deposittype AS ENUM (
    'percentage',
    'fixed_amount'
);


ALTER TYPE public.deposittype OWNER TO postgres;

--
-- Name: feetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.feetype AS ENUM (
    'percentage',
    'fixed_amount'
);


ALTER TYPE public.feetype OWNER TO postgres;

--
-- Name: interestmethod; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.interestmethod AS ENUM (
    'flat',
    'reducing_balance',
    'compound'
);


ALTER TYPE public.interestmethod OWNER TO postgres;

--
-- Name: interestperiod; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.interestperiod AS ENUM (
    'monthly',
    'yearly'
);


ALTER TYPE public.interestperiod OWNER TO postgres;

--
-- Name: latepaymentpenaltytype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.latepaymentpenaltytype AS ENUM (
    'percentage',
    'fixed_amount'
);


ALTER TYPE public.latepaymentpenaltytype OWNER TO postgres;

--
-- Name: loanstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.loanstatus AS ENUM (
    'pending_application',
    'active',
    'closed',
    'written_off',
    'appraised',
    'approved',
    'watchful',
    'non_performing',
    'doubtful',
    'rejected'
);


ALTER TYPE public.loanstatus OWNER TO postgres;

--
-- Name: offsetcovertype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.offsetcovertype AS ENUM (
    'savings',
    'security',
    'both'
);


ALTER TYPE public.offsetcovertype OWNER TO postgres;

--
-- Name: penaltybasis; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.penaltybasis AS ENUM (
    'fixed_amount',
    'percent_of_balance',
    'percent_of_principal'
);


ALTER TYPE public.penaltybasis OWNER TO postgres;

--
-- Name: penaltytrigger; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.penaltytrigger AS ENUM (
    'late_payment',
    'missed_payment',
    'meeting_absence'
);


ALTER TYPE public.penaltytrigger OWNER TO postgres;

--
-- Name: repaymentfrequency; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.repaymentfrequency AS ENUM (
    'daily',
    'weekly',
    'monthly',
    'yearly'
);


ALTER TYPE public.repaymentfrequency OWNER TO postgres;

--
-- Name: securitytype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.securitytype AS ENUM (
    'percentage',
    'fixed_amount',
    'custom_text'
);


ALTER TYPE public.securitytype OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_log (
    id integer NOT NULL,
    entity_type character varying(100) NOT NULL,
    entity_id integer NOT NULL,
    action character varying(100) NOT NULL,
    details text,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_log OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_log_id_seq OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: ledger_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ledger_transactions (
    id integer NOT NULL,
    account_name character varying(255) NOT NULL,
    description character varying(500) NOT NULL,
    money_in numeric(15,2),
    money_out numeric(15,2),
    related_loan_id integer,
    transaction_date date NOT NULL,
    is_reversed boolean NOT NULL,
    reversal_of_transaction_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ledger_transactions OWNER TO postgres;

--
-- Name: ledger_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ledger_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ledger_transactions_id_seq OWNER TO postgres;

--
-- Name: ledger_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ledger_transactions_id_seq OWNED BY public.ledger_transactions.id;


--
-- Name: loan_product_fees; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loan_product_fees (
    id integer NOT NULL,
    loan_product_id integer NOT NULL,
    fee_name character varying(255) NOT NULL,
    fee_type public.feetype NOT NULL,
    fee_value numeric(15,4) NOT NULL,
    affects_principal boolean NOT NULL,
    show_in_statement boolean NOT NULL,
    ledger_account_name character varying(255) NOT NULL
);


ALTER TABLE public.loan_product_fees OWNER TO postgres;

--
-- Name: loan_product_fees_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loan_product_fees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_product_fees_id_seq OWNER TO postgres;

--
-- Name: loan_product_fees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loan_product_fees_id_seq OWNED BY public.loan_product_fees.id;


--
-- Name: loan_product_penalties; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loan_product_penalties (
    id integer NOT NULL,
    loan_product_id integer NOT NULL,
    penalty_name character varying(255) NOT NULL,
    trigger public.penaltytrigger NOT NULL,
    basis public.penaltybasis NOT NULL,
    value numeric(15,4) NOT NULL,
    is_active boolean NOT NULL,
    ledger_account_name character varying(255) NOT NULL
);


ALTER TABLE public.loan_product_penalties OWNER TO postgres;

--
-- Name: loan_product_penalties_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loan_product_penalties_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_product_penalties_id_seq OWNER TO postgres;

--
-- Name: loan_product_penalties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loan_product_penalties_id_seq OWNED BY public.loan_product_penalties.id;


--
-- Name: loan_products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loan_products (
    id integer NOT NULL,
    product_code character varying(50) NOT NULL,
    version_number integer NOT NULL,
    product_name character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    effective_date date NOT NULL,
    interest_method public.interestmethod NOT NULL,
    interest_rate numeric(8,4) NOT NULL,
    interest_period public.interestperiod NOT NULL,
    repayment_frequency public.repaymentfrequency NOT NULL,
    max_repayment_period integer,
    requires_guarantor boolean NOT NULL,
    is_multiple_of_savings boolean NOT NULL,
    savings_multiplier numeric(8,4),
    requires_security boolean NOT NULL,
    security_type public.securitytype,
    security_value numeric(15,2),
    security_notes text,
    requires_deposit boolean NOT NULL,
    deposit_type public.deposittype,
    deposit_value numeric(15,2),
    late_payment_penalty_type public.latepaymentpenaltytype,
    late_payment_penalty_value numeric(15,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    requires_appraisal boolean DEFAULT false NOT NULL,
    requires_board_approval boolean DEFAULT false NOT NULL,
    watchful_after_days integer,
    non_performing_after_days integer,
    doubtful_after_days integer,
    allows_rescheduling boolean DEFAULT false NOT NULL,
    reschedule_fee_type public.latepaymentpenaltytype,
    reschedule_fee_value numeric(15,2),
    allows_offset boolean DEFAULT false NOT NULL,
    offset_covers public.offsetcovertype,
    offset_fee_type public.latepaymentpenaltytype,
    offset_fee_value numeric(15,2)
);


ALTER TABLE public.loan_products OWNER TO postgres;

--
-- Name: loan_products_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loan_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_products_id_seq OWNER TO postgres;

--
-- Name: loan_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loan_products_id_seq OWNED BY public.loan_products.id;


--
-- Name: loan_reschedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loan_reschedules (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    reschedule_date date NOT NULL,
    reason text,
    old_num_periods integer NOT NULL,
    old_outstanding_balance numeric(15,2) NOT NULL,
    new_num_periods integer NOT NULL,
    new_installment numeric(15,2) NOT NULL,
    fee_charged numeric(15,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.loan_reschedules OWNER TO postgres;

--
-- Name: loan_reschedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loan_reschedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_reschedules_id_seq OWNER TO postgres;

--
-- Name: loan_reschedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loan_reschedules_id_seq OWNED BY public.loan_reschedules.id;


--
-- Name: loan_schedule_entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loan_schedule_entries (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    period_number integer NOT NULL,
    due_date date NOT NULL,
    expected_amount numeric(15,2) NOT NULL,
    expected_principal numeric(15,2) NOT NULL,
    expected_interest numeric(15,2) NOT NULL,
    opening_balance numeric(15,2) NOT NULL,
    closing_balance numeric(15,2) NOT NULL,
    is_paid boolean NOT NULL,
    is_missed boolean NOT NULL,
    is_cancelled boolean NOT NULL,
    amount_actually_paid numeric(15,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.loan_schedule_entries OWNER TO postgres;

--
-- Name: loan_schedule_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loan_schedule_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_schedule_entries_id_seq OWNER TO postgres;

--
-- Name: loan_schedule_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loan_schedule_entries_id_seq OWNED BY public.loan_schedule_entries.id;


--
-- Name: loans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loans (
    id integer NOT NULL,
    loan_number character varying(50) NOT NULL,
    member_id integer NOT NULL,
    loan_product_id integer NOT NULL,
    guarantor_member_id integer,
    principal_amount numeric(15,2) NOT NULL,
    security_provided_value numeric(15,2),
    security_provided_notes text,
    deposit_paid_amount numeric(15,2),
    application_date date NOT NULL,
    disbursement_date date,
    status public.loanstatus NOT NULL,
    outstanding_balance numeric(15,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    num_periods integer,
    appraisal_notes text,
    approval_notes text,
    rejection_reason text,
    days_overdue integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.loans OWNER TO postgres;

--
-- Name: loans_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loans_id_seq OWNER TO postgres;

--
-- Name: loans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loans_id_seq OWNED BY public.loans.id;


--
-- Name: member_credit_scores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.member_credit_scores (
    id integer NOT NULL,
    member_id integer NOT NULL,
    score integer NOT NULL,
    label character varying(20) NOT NULL,
    on_time_payments integer NOT NULL,
    underpayments integer NOT NULL,
    missed_payments integer NOT NULL,
    loans_closed_on_time integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.member_credit_scores OWNER TO postgres;

--
-- Name: member_credit_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.member_credit_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.member_credit_scores_id_seq OWNER TO postgres;

--
-- Name: member_credit_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.member_credit_scores_id_seq OWNED BY public.member_credit_scores.id;


--
-- Name: members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.members (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    phone character varying(20),
    savings_balance numeric(15,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_blacklisted boolean DEFAULT false NOT NULL,
    blacklist_reason character varying(500)
);


ALTER TABLE public.members OWNER TO postgres;

--
-- Name: members_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.members_id_seq OWNER TO postgres;

--
-- Name: members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.members_id_seq OWNED BY public.members.id;


--
-- Name: repayments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.repayments (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    payment_date date NOT NULL,
    amount_paid numeric(15,2) NOT NULL,
    amount_to_penalty numeric(15,2) NOT NULL,
    amount_to_interest numeric(15,2) NOT NULL,
    amount_to_principal numeric(15,2) NOT NULL,
    remaining_balance_after numeric(15,2) NOT NULL,
    is_underpaid boolean NOT NULL,
    is_overpaid boolean NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.repayments OWNER TO postgres;

--
-- Name: repayments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.repayments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.repayments_id_seq OWNER TO postgres;

--
-- Name: repayments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.repayments_id_seq OWNED BY public.repayments.id;


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: ledger_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ledger_transactions ALTER COLUMN id SET DEFAULT nextval('public.ledger_transactions_id_seq'::regclass);


--
-- Name: loan_product_fees id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_product_fees ALTER COLUMN id SET DEFAULT nextval('public.loan_product_fees_id_seq'::regclass);


--
-- Name: loan_product_penalties id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_product_penalties ALTER COLUMN id SET DEFAULT nextval('public.loan_product_penalties_id_seq'::regclass);


--
-- Name: loan_products id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_products ALTER COLUMN id SET DEFAULT nextval('public.loan_products_id_seq'::regclass);


--
-- Name: loan_reschedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_reschedules ALTER COLUMN id SET DEFAULT nextval('public.loan_reschedules_id_seq'::regclass);


--
-- Name: loan_schedule_entries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_schedule_entries ALTER COLUMN id SET DEFAULT nextval('public.loan_schedule_entries_id_seq'::regclass);


--
-- Name: loans id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loans ALTER COLUMN id SET DEFAULT nextval('public.loans_id_seq'::regclass);


--
-- Name: member_credit_scores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member_credit_scores ALTER COLUMN id SET DEFAULT nextval('public.member_credit_scores_id_seq'::regclass);


--
-- Name: members id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.members ALTER COLUMN id SET DEFAULT nextval('public.members_id_seq'::regclass);


--
-- Name: repayments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.repayments ALTER COLUMN id SET DEFAULT nextval('public.repayments_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
f0c16912f886
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_log (id, entity_type, entity_id, action, details, "timestamp") FROM stdin;
1	loan_product	1	created	{"product_code": "EMERGENCY_LOAN", "version": 1, "product_name": "Emergency Loan"}	2026-07-13 10:21:01.618017+03
2	loan	1	created	{"loan_number": "LN-20260713-00001", "member": "Bram", "product_id": 1, "principal": "5000"}	2026-07-13 11:09:50.197716+03
3	ledger_transaction	1	reversed	{"offset_transaction_id": 2}	2026-07-13 11:10:47.2249+03
4	ledger_transaction	2	created	{"type": "reversal", "reversal_of": 1}	2026-07-13 11:10:47.2249+03
5	loan_product	2	created	{"product_code": "EMERGENCY_LOAN2", "version": 1, "product_name": "Emergency Loan"}	2026-07-14 02:38:13.535715+03
6	loan_product	2	deleted	{"product_code": "EMERGENCY_LOAN2"}	2026-07-14 02:38:19.250156+03
7	loan_product	3	created	{"product_code": "EMERGENCY_LOAN2", "version": 1, "product_name": "Emergency Loan"}	2026-07-14 02:51:44.76701+03
8	loan_product	3	deleted	{"product_code": "EMERGENCY_LOAN2"}	2026-07-14 02:51:56.66033+03
9	loan	2	created	{"loan_number": "LN-20260714-00001", "member": "Brian Otieno", "product_id": 1, "principal": "8888", "status": "approved"}	2026-07-14 03:00:15.806331+03
10	loan	2	disbursed	{"date": "2026-07-14"}	2026-07-14 03:08:12.559421+03
11	loan	1	deleted	{"loan_number": "LN-20260713-00001"}	2026-07-14 03:08:24.336972+03
12	loan	3	created	{"loan_number": "LN-20260714-00002", "member": "Alice Wanjiku", "product_id": 1, "principal": "6000", "status": "approved"}	2026-07-14 03:14:11.450889+03
13	loan_product	4	created	{"product_code": "EMERGENCY_LOAN2", "version": 1, "product_name": "Emergency Loan"}	2026-07-14 03:14:59.982648+03
14	loan	3	disbursed	{"date": "2026-07-14"}	2026-07-14 03:15:28.263275+03
\.


--
-- Data for Name: ledger_transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ledger_transactions (id, account_name, description, money_in, money_out, related_loan_id, transaction_date, is_reversed, reversal_of_transaction_id, created_at) FROM stdin;
3	Jiinue Loan Account	Loan disbursement — LN-20260714-00001 to Brian Otieno	\N	8888.00	2	2026-07-14	f	\N	2026-07-14 03:08:12.559421+03
4	Jiinue Loan Account	Loan disbursement — LN-20260714-00002 to Alice Wanjiku	\N	6000.00	3	2026-07-14	f	\N	2026-07-14 03:15:28.263275+03
\.


--
-- Data for Name: loan_product_fees; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loan_product_fees (id, loan_product_id, fee_name, fee_type, fee_value, affects_principal, show_in_statement, ledger_account_name) FROM stdin;
\.


--
-- Data for Name: loan_product_penalties; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loan_product_penalties (id, loan_product_id, penalty_name, trigger, basis, value, is_active, ledger_account_name) FROM stdin;
\.


--
-- Data for Name: loan_products; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loan_products (id, product_code, version_number, product_name, is_active, effective_date, interest_method, interest_rate, interest_period, repayment_frequency, max_repayment_period, requires_guarantor, is_multiple_of_savings, savings_multiplier, requires_security, security_type, security_value, security_notes, requires_deposit, deposit_type, deposit_value, late_payment_penalty_type, late_payment_penalty_value, created_at, updated_at, requires_appraisal, requires_board_approval, watchful_after_days, non_performing_after_days, doubtful_after_days, allows_rescheduling, reschedule_fee_type, reschedule_fee_value, allows_offset, offset_covers, offset_fee_type, offset_fee_value) FROM stdin;
1	EMERGENCY_LOAN	1	Emergency Loan	t	2026-07-13	reducing_balance	5.0000	monthly	daily	6	t	f	\N	f	\N	\N	\N	f	\N	\N	\N	5000.00	2026-07-13 10:21:01.618017+03	2026-07-13 10:21:01.618017+03	f	f	\N	\N	\N	f	\N	\N	f	\N	\N	\N
4	EMERGENCY_LOAN2	1	Emergency Loan	t	2026-07-09	flat	8.0000	monthly	daily	\N	t	f	\N	t	percentage	25.00	\N	f	\N	\N	percentage	10.00	2026-07-14 03:14:59.982648+03	2026-07-14 03:14:59.982648+03	f	f	30	90	180	f	\N	\N	f	\N	\N	\N
\.


--
-- Data for Name: loan_reschedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loan_reschedules (id, loan_id, reschedule_date, reason, old_num_periods, old_outstanding_balance, new_num_periods, new_installment, fee_charged, created_at) FROM stdin;
\.


--
-- Data for Name: loan_schedule_entries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loan_schedule_entries (id, loan_id, period_number, due_date, expected_amount, expected_principal, expected_interest, opening_balance, closing_balance, is_paid, is_missed, is_cancelled, amount_actually_paid, created_at) FROM stdin;
1	2	1	2026-07-15	1489.87	1475.26	14.61	8888.00	7412.74	f	f	f	0.00	2026-07-14 03:08:12.559421+03
2	2	2	2026-07-16	1489.87	1477.68	12.19	7412.74	5935.06	f	f	f	0.00	2026-07-14 03:08:12.559421+03
3	2	3	2026-07-17	1489.87	1480.11	9.76	5935.06	4454.95	f	f	f	0.00	2026-07-14 03:08:12.559421+03
4	2	4	2026-07-18	1489.87	1482.54	7.32	4454.95	2972.40	f	f	f	0.00	2026-07-14 03:08:12.559421+03
5	2	5	2026-07-19	1489.87	1484.98	4.89	2972.40	1487.42	f	f	f	0.00	2026-07-14 03:08:12.559421+03
6	2	6	2026-07-20	1489.87	1487.42	2.45	1487.42	0.00	f	f	f	0.00	2026-07-14 03:08:12.559421+03
7	3	1	2026-07-15	862.79	852.93	9.86	6000.00	5147.07	f	f	f	0.00	2026-07-14 03:15:28.263275+03
8	3	2	2026-07-16	862.79	854.33	8.46	5147.07	4292.75	f	f	f	0.00	2026-07-14 03:15:28.263275+03
9	3	3	2026-07-17	862.79	855.73	7.06	4292.75	3437.02	f	f	f	0.00	2026-07-14 03:15:28.263275+03
10	3	4	2026-07-18	862.79	857.14	5.65	3437.02	2579.88	f	f	f	0.00	2026-07-14 03:15:28.263275+03
11	3	5	2026-07-19	862.79	858.55	4.24	2579.88	1721.33	f	f	f	0.00	2026-07-14 03:15:28.263275+03
12	3	6	2026-07-20	862.79	859.96	2.83	1721.33	861.37	f	f	f	0.00	2026-07-14 03:15:28.263275+03
13	3	7	2026-07-21	862.79	861.37	1.42	861.37	0.00	f	f	f	0.00	2026-07-14 03:15:28.263275+03
\.


--
-- Data for Name: loans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loans (id, loan_number, member_id, loan_product_id, guarantor_member_id, principal_amount, security_provided_value, security_provided_notes, deposit_paid_amount, application_date, disbursement_date, status, outstanding_balance, created_at, num_periods, appraisal_notes, approval_notes, rejection_reason, days_overdue) FROM stdin;
2	LN-20260714-00001	2	1	9	8888.00	\N	\N	\N	2026-07-14	2026-07-14	active	8888.00	2026-07-14 03:00:15.806331+03	6	\N	\N	\N	0
3	LN-20260714-00002	1	1	10	6000.00	\N	\N	\N	2026-07-14	2026-07-14	active	6000.00	2026-07-14 03:14:11.450889+03	7	\N	\N	\N	0
\.


--
-- Data for Name: member_credit_scores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.member_credit_scores (id, member_id, score, label, on_time_payments, underpayments, missed_payments, loans_closed_on_time, updated_at) FROM stdin;
\.


--
-- Data for Name: members; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.members (id, name, phone, savings_balance, created_at, is_blacklisted, blacklist_reason) FROM stdin;
1	Alice Wanjiku	0712 345 678	150000.00	2026-07-13 09:46:23.532175+03	f	\N
2	Brian Otieno	0723 456 789	45000.00	2026-07-13 09:46:23.532175+03	f	\N
3	Catherine Njeri	0734 567 890	320000.00	2026-07-13 09:46:23.532175+03	f	\N
4	David Kamau	0745 678 901	8000.00	2026-07-13 09:46:23.532175+03	f	\N
5	Esther Achieng	0756 789 012	210000.00	2026-07-13 09:46:23.532175+03	f	\N
6	Francis Mwangi	0767 890 123	60000.00	2026-07-13 09:46:23.532175+03	f	\N
7	Grace Chebet	0778 901 234	95000.00	2026-07-13 09:46:23.532175+03	f	\N
8	Hassan Omar	0789 012 345	0.00	2026-07-13 09:46:23.532175+03	f	\N
9	Irene Mutua	0790 123 456	500000.00	2026-07-13 09:46:23.532175+03	f	\N
10	James Kariuki	0701 234 567	33000.00	2026-07-13 09:46:23.532175+03	f	\N
11	Bram	+254741797609	50000.00	2026-07-13 10:37:14.428626+03	f	\N
12	Bramwel Oranga	34543	0.03	2026-07-14 02:29:56.351772+03	f	\N
\.


--
-- Data for Name: repayments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.repayments (id, loan_id, payment_date, amount_paid, amount_to_penalty, amount_to_interest, amount_to_principal, remaining_balance_after, is_underpaid, is_overpaid, notes, created_at) FROM stdin;
\.


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 14, true);


--
-- Name: ledger_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ledger_transactions_id_seq', 4, true);


--
-- Name: loan_product_fees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loan_product_fees_id_seq', 1, false);


--
-- Name: loan_product_penalties_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loan_product_penalties_id_seq', 1, false);


--
-- Name: loan_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loan_products_id_seq', 4, true);


--
-- Name: loan_reschedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loan_reschedules_id_seq', 1, false);


--
-- Name: loan_schedule_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loan_schedule_entries_id_seq', 13, true);


--
-- Name: loans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loans_id_seq', 3, true);


--
-- Name: member_credit_scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.member_credit_scores_id_seq', 1, false);


--
-- Name: members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.members_id_seq', 12, true);


--
-- Name: repayments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.repayments_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: ledger_transactions ledger_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ledger_transactions
    ADD CONSTRAINT ledger_transactions_pkey PRIMARY KEY (id);


--
-- Name: loan_product_fees loan_product_fees_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_product_fees
    ADD CONSTRAINT loan_product_fees_pkey PRIMARY KEY (id);


--
-- Name: loan_product_penalties loan_product_penalties_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_product_penalties
    ADD CONSTRAINT loan_product_penalties_pkey PRIMARY KEY (id);


--
-- Name: loan_products loan_products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_products
    ADD CONSTRAINT loan_products_pkey PRIMARY KEY (id);


--
-- Name: loan_reschedules loan_reschedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_reschedules
    ADD CONSTRAINT loan_reschedules_pkey PRIMARY KEY (id);


--
-- Name: loan_schedule_entries loan_schedule_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_schedule_entries
    ADD CONSTRAINT loan_schedule_entries_pkey PRIMARY KEY (id);


--
-- Name: loans loans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pkey PRIMARY KEY (id);


--
-- Name: member_credit_scores member_credit_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member_credit_scores
    ADD CONSTRAINT member_credit_scores_pkey PRIMARY KEY (id);


--
-- Name: members members_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.members
    ADD CONSTRAINT members_pkey PRIMARY KEY (id);


--
-- Name: repayments repayments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_log_entity_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_entity_id ON public.audit_log USING btree (entity_id);


--
-- Name: ix_audit_log_entity_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_entity_type ON public.audit_log USING btree (entity_type);


--
-- Name: ix_audit_log_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_id ON public.audit_log USING btree (id);


--
-- Name: ix_audit_log_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_timestamp ON public.audit_log USING btree ("timestamp");


--
-- Name: ix_ledger_transactions_account_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ledger_transactions_account_name ON public.ledger_transactions USING btree (account_name);


--
-- Name: ix_ledger_transactions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ledger_transactions_id ON public.ledger_transactions USING btree (id);


--
-- Name: ix_ledger_transactions_related_loan_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ledger_transactions_related_loan_id ON public.ledger_transactions USING btree (related_loan_id);


--
-- Name: ix_loan_product_fees_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_product_fees_id ON public.loan_product_fees USING btree (id);


--
-- Name: ix_loan_product_penalties_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_product_penalties_id ON public.loan_product_penalties USING btree (id);


--
-- Name: ix_loan_product_penalties_loan_product_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_product_penalties_loan_product_id ON public.loan_product_penalties USING btree (loan_product_id);


--
-- Name: ix_loan_products_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_products_id ON public.loan_products USING btree (id);


--
-- Name: ix_loan_products_product_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_products_product_code ON public.loan_products USING btree (product_code);


--
-- Name: ix_loan_reschedules_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_reschedules_id ON public.loan_reschedules USING btree (id);


--
-- Name: ix_loan_reschedules_loan_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_reschedules_loan_id ON public.loan_reschedules USING btree (loan_id);


--
-- Name: ix_loan_schedule_entries_due_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_schedule_entries_due_date ON public.loan_schedule_entries USING btree (due_date);


--
-- Name: ix_loan_schedule_entries_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_schedule_entries_id ON public.loan_schedule_entries USING btree (id);


--
-- Name: ix_loan_schedule_entries_loan_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loan_schedule_entries_loan_id ON public.loan_schedule_entries USING btree (loan_id);


--
-- Name: ix_loans_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loans_id ON public.loans USING btree (id);


--
-- Name: ix_loans_loan_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_loans_loan_number ON public.loans USING btree (loan_number);


--
-- Name: ix_member_credit_scores_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_member_credit_scores_id ON public.member_credit_scores USING btree (id);


--
-- Name: ix_member_credit_scores_member_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_member_credit_scores_member_id ON public.member_credit_scores USING btree (member_id);


--
-- Name: ix_members_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_members_id ON public.members USING btree (id);


--
-- Name: ix_repayments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_repayments_id ON public.repayments USING btree (id);


--
-- Name: ix_repayments_loan_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_repayments_loan_id ON public.repayments USING btree (loan_id);


--
-- Name: ledger_transactions fk_reversal_self; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ledger_transactions
    ADD CONSTRAINT fk_reversal_self FOREIGN KEY (reversal_of_transaction_id) REFERENCES public.ledger_transactions(id);


--
-- Name: ledger_transactions ledger_transactions_related_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ledger_transactions
    ADD CONSTRAINT ledger_transactions_related_loan_id_fkey FOREIGN KEY (related_loan_id) REFERENCES public.loans(id);


--
-- Name: loan_product_fees loan_product_fees_loan_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_product_fees
    ADD CONSTRAINT loan_product_fees_loan_product_id_fkey FOREIGN KEY (loan_product_id) REFERENCES public.loan_products(id) ON DELETE CASCADE;


--
-- Name: loan_product_penalties loan_product_penalties_loan_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_product_penalties
    ADD CONSTRAINT loan_product_penalties_loan_product_id_fkey FOREIGN KEY (loan_product_id) REFERENCES public.loan_products(id) ON DELETE CASCADE;


--
-- Name: loan_reschedules loan_reschedules_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_reschedules
    ADD CONSTRAINT loan_reschedules_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loans(id) ON DELETE CASCADE;


--
-- Name: loan_schedule_entries loan_schedule_entries_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_schedule_entries
    ADD CONSTRAINT loan_schedule_entries_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loans(id) ON DELETE CASCADE;


--
-- Name: loans loans_guarantor_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_guarantor_member_id_fkey FOREIGN KEY (guarantor_member_id) REFERENCES public.members(id);


--
-- Name: loans loans_loan_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_loan_product_id_fkey FOREIGN KEY (loan_product_id) REFERENCES public.loan_products(id);


--
-- Name: loans loans_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_member_id_fkey FOREIGN KEY (member_id) REFERENCES public.members(id);


--
-- Name: member_credit_scores member_credit_scores_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member_credit_scores
    ADD CONSTRAINT member_credit_scores_member_id_fkey FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE;


--
-- Name: repayments repayments_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loans(id);


--
-- PostgreSQL database dump complete
--

\unrestrict vUSxP2qYM0kgFA49dbf9UB8Cod7CfPXrzGVsY1YA7f2ftRz0FIar9KQbAV0IlGe

