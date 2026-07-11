create table contract_role_assignments (
    contract_id text not null references contracts(id),
    user_id text not null references users(id),
    role text not null check (role in ('configuration_administrator', 'auditor')),
    agency_organization_id text not null references organizations(id),
    created_at timestamptz not null default now(),
    primary key (contract_id, user_id, role)
);

create or replace function validate_contract_role_assignment() returns trigger language plpgsql as $$
begin
    if not exists (
        select 1
        from contracts c
        join users u on u.id = new.user_id
        where c.id = new.contract_id
          and c.agency_organization_id = new.agency_organization_id
          and u.role = new.role
          and u.active = true
    ) then
        raise exception 'contract role assignment must match canonical contract and active user';
    end if;
    return new;
end;
$$;

create trigger contract_role_assignments_validate
before insert or update on contract_role_assignments
for each row execute function validate_contract_role_assignment();

create index contract_role_assignments_user_idx
on contract_role_assignments(user_id, role, contract_id);
