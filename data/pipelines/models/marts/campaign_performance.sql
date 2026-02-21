with campaigns as (
    select * from {{ source('aima', 'campaigns') }}
    where status = 'completed'
),

performance as (
    select
        id                  as campaign_id,
        org_id,
        name,
        channel,
        target_segment_id,
        subject_line,
        offer_type,
        offer_value,
        budget,

        predicted_open_rate,
        predicted_click_rate,
        predicted_conversion_rate,
        predicted_revenue,
        predicted_roi,

        actual_open_rate,
        actual_click_rate,
        actual_conversion_rate,
        actual_revenue,
        coalesce(actual_revenue, 0) / nullif(budget, 0) as actual_roi,

        actual_open_rate - predicted_open_rate          as open_rate_delta,
        actual_click_rate - predicted_click_rate        as click_rate_delta,
        actual_conversion_rate - predicted_conversion_rate as conversion_delta,
        actual_revenue - predicted_revenue              as revenue_delta,

        case
            when abs(actual_open_rate - predicted_open_rate) <= 0.05 then 'accurate'
            when actual_open_rate > predicted_open_rate then 'over_predicted'
            else 'under_predicted'
        end as prediction_accuracy,

        launched_at,
        completed_at,
        extract(day from completed_at - launched_at) as campaign_duration_days,
        date_trunc('month', launched_at) as launch_month

    from campaigns
    where launched_at is not null
)

select * from performance
