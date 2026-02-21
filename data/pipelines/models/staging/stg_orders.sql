with source as (
    select * from {{ source('aima', 'orders') }}
),

cleaned as (
    select
        id                          as order_id,
        org_id,
        customer_id,
        connector_id,
        external_id,
        order_number,
        status,
        currency,
        coalesce(subtotal, total)   as subtotal,
        total,
        coalesce(discount_total, 0) as discount_total,
        coalesce(tax_total, 0)      as tax_total,
        total - coalesce(discount_total, 0) as net_revenue,
        items,
        jsonb_array_length(coalesce(items, '[]'::jsonb)) as item_count,
        channel,
        properties,
        ordered_at,
        date_trunc('day', ordered_at)   as order_date,
        date_trunc('week', ordered_at)  as order_week,
        date_trunc('month', ordered_at) as order_month,
        date_part('year', ordered_at)   as order_year,
        date_part('month', ordered_at)  as order_month_num,
        date_part('dow', ordered_at)    as order_day_of_week,
        date_part('hour', ordered_at)   as order_hour,
        date_part('quarter', ordered_at) as order_quarter

    from source
    where total > 0
      and ordered_at is not null
      and status not in ('cancelled', 'refunded')
)

select * from cleaned
