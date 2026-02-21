with source as (
    select * from {{ source('aima', 'customer_events') }}
),

renamed as (
    select
        id              as event_id,
        org_id,
        customer_id,
        event_type,
        event_data,
        source,
        occurred_at,
        ingested_at,
        date_trunc('hour', occurred_at) as event_hour,
        date_trunc('day', occurred_at)  as event_date,
        date_part('hour', occurred_at)  as hour_of_day,
        date_part('dow', occurred_at)   as day_of_week

    from source
)

select * from renamed
