create table organizations (
    id text primary key,
    name text not null unique,
    kind text not null check (kind in ('government', 'ngo', 'oversight', 'platform'))
);

create table users (
    id text primary key,
    organization_id text not null references organizations(id),
    display_name text not null,
    email text not null unique,
    role text not null,
    password_hash text not null,
    active boolean not null default true
);

create table contracts (
    id text primary key,
    name text not null,
    agency_organization_id text not null references organizations(id),
    ngo_organization_id text not null references organizations(id),
    contract_start date not null,
    contract_end date not null,
    service_period_start date not null,
    service_period_end date not null,
    currency text not null check (currency = 'USD')
);

create table budget_categories (
    id text primary key,
    contract_id text not null references contracts(id),
    name text not null,
    budget_limit numeric(14, 2) not null check (budget_limit >= 0),
    unique (contract_id, name)
);

create table configuration_versions (
    id text primary key,
    contract_id text not null references contracts(id),
    version integer not null check (version > 0),
    status text not null check (status in ('draft', 'active', 'superseded')),
    payload jsonb not null,
    unique (contract_id, version)
);
