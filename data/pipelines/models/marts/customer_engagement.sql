with events as (
    select * from {{ ref('stg_events') }}
),

email_events as (
    select
        org_id,
        customer_id,
        count(*) filter (where event_type = 'email_sent')       as emails_sent,
        count(*) filter (where event_type = 'email_opened')     as emails_opened,
        count(*) filter (where event_type = 'email_clicked')    as emails_clicked,
        count(*) filter (where event_type = 'email_converted')  as emails_converted,
        count(*) filter (where event_type = 'email_bounced')    as emails_bounced,
        count(*) filter (where event_type = 'email_unsubscribed') as unsubscribes

    from events
    where event_type like 'email_%'
    group by 1, 2
),

web_events as (
    select
        org_id,
        customer_id,
        count(*) filter (where event_type = 'session_started')  as sessions,
        count(*) filter (where event_type = 'page_viewed')      as page_views,
        count(*) filter (where event_type = 'cart_added')       as cart_adds,
        count(*) filter (where event_type = 'cart_abandoned')   as cart_abandons,
        count(*) filter (where event_type = 'checkout_started') as checkout_starts,
        avg(
            case when event_type = 'session_ended'
            then (event_data->>'duration_seconds')::int end
        ) as avg_session_seconds

    from events
    where event_type in (
        'session_started', 'page_viewed', 'cart_added',
        'cart_abandoned', 'checkout_started', 'session_ended'
    )
    group by 1, 2
),

final as (
    select
        coalesce(e.org_id, w.org_id)               as org_id,
        coalesce(e.customer_id, w.customer_id)     as customer_id,

        coalesce(e.emails_sent, 0)                  as emails_sent,
        coalesce(e.emails_opened, 0)                as emails_opened,
        coalesce(e.emails_clicked, 0)               as emails_clicked,
        coalesce(e.emails_converted, 0)             as emails_converted,
        coalesce(e.unsubscribes, 0)                 as unsubscribes,

        case when coalesce(e.emails_sent, 0) > 0
            then e.emails_opened::float / e.emails_sent
            else 0 end                              as email_open_rate,

        case when coalesce(e.emails_sent, 0) > 0
            then e.emails_clicked::float / e.emails_sent
            else 0 end                              as email_click_rate,

        coalesce(w.sessions, 0)                     as sessions,
        coalesce(w.page_views, 0)                   as page_views,
        coalesce(w.cart_adds, 0)                    as cart_adds,
        coalesce(w.cart_abandons, 0)                as cart_abandons,
        coalesce(w.avg_session_seconds, 0)          as avg_session_seconds,

        case when coalesce(w.cart_adds, 0) > 0
            then w.cart_abandons::float / w.cart_adds
            else 0 end                              as cart_abandonment_rate

    from email_events e
    full outer join web_events w
        on e.org_id = w.org_id and e.customer_id = w.customer_id
)

select * from final
