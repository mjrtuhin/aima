with orders as (
    select * from {{ ref('stg_orders') }}
),

order_stats as (
    select
        org_id,
        customer_id,
        count(*)                                        as frequency,
        sum(total)                                      as monetary_value,
        avg(total)                                      as avg_order_value,
        max(total)                                      as max_order_value,
        min(total)                                      as min_order_value,
        stddev(total)                                   as order_value_std,
        sum(item_count)                                 as total_items,
        avg(item_count)                                 as avg_items_per_order,
        max(ordered_at)                                 as last_order_at,
        min(ordered_at)                                 as first_order_at,
        current_timestamp - max(ordered_at)             as time_since_last_order,
        extract(day from current_timestamp - max(ordered_at)) as recency_days,
        extract(day from max(ordered_at) - min(ordered_at)) as tenure_days,
        mode() within group (order by order_day_of_week) as preferred_day_of_week,
        mode() within group (order by order_hour)       as preferred_hour_of_day,
        sum(case when order_quarter = 1 then 1 else 0 end)::float / count(*) as q1_share,
        sum(case when order_quarter = 2 then 1 else 0 end)::float / count(*) as q2_share,
        sum(case when order_quarter = 3 then 1 else 0 end)::float / count(*) as q3_share,
        sum(case when order_quarter = 4 then 1 else 0 end)::float / count(*) as q4_share

    from orders
    group by 1, 2
),

with_rfm_scores as (
    select
        *,
        ntile(5) over (partition by org_id order by recency_days asc)    as r_score,
        ntile(5) over (partition by org_id order by frequency asc)        as f_score,
        ntile(5) over (partition by org_id order by monetary_value asc)   as m_score

    from order_stats
),

final as (
    select
        *,
        r_score + f_score + m_score as rfm_total_score,
        concat(r_score::text, f_score::text, m_score::text) as rfm_segment_code,
        case
            when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'
            when r_score >= 3 and f_score >= 3 then 'Loyal Customers'
            when r_score >= 4 and f_score <= 2 then 'New Customers'
            when r_score >= 3 and f_score <= 2 then 'Potential Loyalists'
            when r_score = 3 and f_score >= 3 then 'Need Attention'
            when r_score <= 2 and f_score >= 3 then 'At Risk'
            when r_score <= 2 and m_score >= 4 then 'Cannot Lose Them'
            when r_score <= 2 and f_score <= 2 then 'Hibernating'
            else 'About to Sleep'
        end as rfm_segment_name

    from with_rfm_scores
)

select * from final
