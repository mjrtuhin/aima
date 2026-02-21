with source as (
    select * from {{ source('aima', 'customers') }}
),

renamed as (
    select
        id                          as customer_id,
        org_id,
        external_id,
        connector_id,
        lower(trim(email))          as email,
        trim(first_name)            as first_name,
        trim(last_name)             as last_name,
        trim(coalesce(first_name, '') || ' ' || coalesce(last_name, ''))
                                    as full_name,
        phone,
        upper(country)              as country,
        city,
        timezone,
        tags,
        properties,
        created_at,
        updated_at,
        date_trunc('day', created_at) as signup_date,
        date_part('year', created_at) as signup_year,
        date_part('month', created_at) as signup_month

    from source
    where email is not null
      and email ~ '^[^@]+@[^@]+\.[^@]+$'
)

select * from renamed
