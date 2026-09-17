import csv, random, math
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DATA.mkdir(parents=True, exist_ok=True)
random.seed(20260917)

# ------------------------------
# Company assumptions
# ------------------------------
company_rows = [
    ('company_name', 'GaonWorks Services (가상회사)'),
    ('company_type', '중소·중견 규모 IT 서비스 회사 시뮬레이션'),
    ('industry', 'IT 서비스 / B2B 운영 지원'),
    ('employees', '300'),
    ('offices', '서울 본사 + 1개 지사'),
    ('target_company_size', '약 200~1,000명 규모에서 반복 문의와 내부 문서가 많은 조직에 적합'),
    ('main_question_domains', 'IT, 인사, 총무, 재무, 사내 일반 규정'),
    ('baseline_period', '도입 전 1개월'),
    ('comparison_period', '초기 운영 1개월 → 2개월차 → 3개월차'),
    ('data_notice', '모든 회사/문의/성과 수치는 실제 고객사 내부 데이터가 아닌 프로젝트용 시뮬레이션'),
]
with open(DATA/'company_profile.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['key','value']); w.writerows(company_rows)

# ------------------------------
# Common question pools
# ------------------------------
domains = {
    'IT': [('VPN','VPN 설치/접속 방법 알려줘'),('계정','계정 잠금 해제 방법 알려줘'),('프로그램 설치','업무 프로그램 설치 절차 알려줘'),('네트워크','사내 인터넷 연결이 불안정해')],
    '인사': [('연차','연차 신청 방법 알려줘'),('급여','급여 지급/명세서 확인 방법 알려줘'),('복지','복지포인트 사용 방법 알려줘'),('근태','근태 수정 절차 알려줘')],
    '총무': [('회의실','회의실 예약 방법 알려줘'),('택배/우편','사내 우편 발송 절차 알려줘'),('비품','사무용 비품 신청 방법 알려줘')],
    '재무': [('출장비','출장비 정산 기준 알려줘'),('법인카드','법인카드 정산 방법 알려줘'),('경비','경비 처리 절차 알려줘')],
    '일반규정': [('재택근무','재택근무 규정 알려줘'),('보안','자료 반출 기준 알려줘'),('교육','사내 교육 신청 방법 알려줘')]
}
employee_departments = ['개발','IT운영','영업','기획','인사','재무','디자인','고객지원']
support_dept_map = {'IT':'IT지원팀','인사':'인사팀','총무':'총무팀','재무':'재무팀','일반규정':'경영지원팀'}

# ------------------------------
# Baseline: 250 pre-chatbot inquiries
# response_wait_minutes = 직원이 질문을 보낸 뒤 최종 답변을 받을 때까지의 전체 대기시간
# answering_minutes = 지원부서 직원이 실제 답변 작성/처리에 투입한 시간
# ------------------------------
baseline = []
start = datetime(2026,5,1,8,0)
for i in range(250):
    category = random.choices(list(domains), weights=[34,25,16,15,10])[0]
    topic, _ = random.choice(domains[category])
    source = random.choices(['support_department','coworker','senior','internal_document'], weights=[42,26,20,12])[0]
    search = max(0.5, random.gauss(6.7, 2.4))
    asking = max(0.3, random.gauss(2.0, 0.8))
    # Waiting time is end-user elapsed time, not support staff labor time.
    if source == 'support_department':
        wait = max(4.0, random.gauss(43.0, 20.0))
        answering = max(2.0, random.gauss(8.5, 3.0))
    elif source in ('coworker','senior'):
        wait = max(1.0, random.gauss(16.0, 9.0))
        answering = max(1.0, random.gauss(5.0, 2.0))
    else:
        wait = max(0.5, random.gauss(7.0, 3.5))
        answering = 0.0
    resolved = 1 if random.random() < 0.94 else 0
    created = start + timedelta(minutes=random.randint(0, 30*24*60-1))
    baseline.append({
        'inquiry_id':f'B{i+1:04d}', 'created_at':created.strftime('%Y-%m-%d %H:%M:%S'),
        'employee_id':f'E{random.randint(1,300):04d}', 'employee_department':random.choice(employee_departments),
        'support_department':support_dept_map[category] if source=='support_department' else '',
        'category':category,'topic':topic,'source':source,
        'search_minutes':round(search,1),'asking_minutes':round(asking,1),
        'response_wait_minutes':round(wait,1),'answering_minutes':round(answering,1),
        'resolved':resolved,'period':'pre_chatbot_1m'
    })

baseline_fields = list(baseline[0].keys())
with open(DATA/'baseline_peer_inquiries.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=baseline_fields); w.writeheader(); w.writerows(baseline)

# Baseline summary
support_rows = [x for x in baseline if x['source']=='support_department']
summary = {
    'monthly_direct_inquiries': len(baseline),
    'avg_search_minutes': round(mean(x['search_minutes'] for x in baseline),1),
    'avg_asking_minutes': round(mean(x['asking_minutes'] for x in baseline),1),
    'avg_response_wait_minutes_all_sources': round(mean(x['response_wait_minutes'] for x in baseline),1),
    'avg_support_department_response_wait_minutes': round(mean(x['response_wait_minutes'] for x in support_rows),1),
    'avg_support_department_answering_minutes': round(mean(x['answering_minutes'] for x in support_rows),1),
    'resolved_rate_pct': round(sum(x['resolved'] for x in baseline)/len(baseline)*100,1),
    'support_department_share_pct': round(len(support_rows)/len(baseline)*100,1),
}
with open(DATA/'baseline_summary.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['metric','value']); w.writerows(summary.items())

# ------------------------------
# Chatbot period configs
# answer_source/route shares are mutually exclusive.
# LLM API call rate = RAG + direct LLM because RAG answer generation also invokes the LLM.
# ------------------------------
configs = {
    'initial_1m': {
        'start': datetime(2026,6,1,8,0), 'n':600,
        'route_counts': {'FAQ':48,'RAG':72,'LLM':432,'RULE':48},
        'resolved_counts': {'FAQ':41,'RAG':32,'LLM':107,'RULE':0},
        'recontact':228,'peer_reask':264,
        'api_error_rate':0.026,'retry_rate':0.070,
    },
    'month2': {
        'start': datetime(2026,7,1,8,0), 'n':720,
        'route_counts': {'FAQ':94,'RAG':130,'LLM':438,'RULE':58},
        'resolved_counts': {'FAQ':85,'RAG':71,'LLM':111,'RULE':0},
        'recontact':238,'peer_reask':274,
        'api_error_rate':0.022,'retry_rate':0.060,
    },
    'month3': {
        'start': datetime(2026,8,1,8,0), 'n':850,
        'route_counts': {'FAQ':153,'RAG':204,'LLM':425,'RULE':68},
        'resolved_counts': {'FAQ':145,'RAG':133,'LLM':105,'RULE':0},
        'recontact':238,'peer_reask':272,
        'api_error_rate':0.018,'retry_rate':0.050,
    },
}

requests=[]
req_seq=1
conv_seq=1
for period,cfg in configs.items():
    route_list=[]
    for route,count in cfg['route_counts'].items(): route_list += [route]*count
    random.shuffle(route_list)

    # Exact resolved counts by route
    resolved_flags=[]
    for route,count in cfg['route_counts'].items():
        flags=[1]*cfg['resolved_counts'][route]+[0]*(count-cfg['resolved_counts'][route])
        random.shuffle(flags)
        resolved_flags += [(route,x) for x in flags]
    # Match shuffled route_list to per-route pools
    pools={r:[x for rr,x in resolved_flags if rr==r] for r in cfg['route_counts']}
    for r in pools: random.shuffle(pools[r])

    # Exact recontact/peer flags assigned independently, weighted toward unresolved later in loop.
    rec_indices=set(random.sample(range(cfg['n']), cfg['recontact']))
    peer_indices=set(random.sample(range(cfg['n']), cfg['peer_reask']))

    for idx, route in enumerate(route_list):
        category = random.choices(list(domains), weights=[34,25,16,15,10])[0]
        topic, question = random.choice(domains[category])
        resolved = pools[route].pop()
        created = cfg['start'] + timedelta(minutes=random.randint(0, 29*24*60-1))
        if route=='FAQ':
            answer_source='FAQ'; kv=f'faq_{topic}_v{2 if period=="month3" else 1}'
            inp=out=0; resp=random.uniform(0.2,0.9); calls=0
        elif route=='RULE':
            answer_source='RULE'; kv=''; inp=out=0; resp=random.uniform(0.2,0.7); calls=0
        elif route=='RAG':
            answer_source='RAG'; kv=f'{topic}_guide_v{2 if period=="month3" else 1}'
            if period=='initial_1m': inp=random.randint(1400,2500); out=random.randint(220,520); resp=random.uniform(3.0,7.5)
            elif period=='month2': inp=random.randint(1100,2100); out=random.randint(200,480); resp=random.uniform(2.7,6.7)
            else: inp=random.randint(850,1750); out=random.randint(180,440); resp=random.uniform(2.4,5.9)
            calls=1
        else:
            answer_source='LLM'; kv=''
            if period=='initial_1m': inp=random.randint(1200,2600); out=random.randint(250,720); resp=random.uniform(3.2,8.2)
            elif period=='month2': inp=random.randint(1100,2350); out=random.randint(230,660); resp=random.uniform(3.0,7.4)
            else: inp=random.randint(1000,2150); out=random.randint(220,620); resp=random.uniform(2.8,6.8)
            calls=1

        retry=0; status=200; err=''
        if calls:
            if random.random() < cfg['retry_rate']:
                retry=random.choice([1,1,1,2]); calls += retry
            if random.random() < cfg['api_error_rate']:
                status=random.choice([429,500,504]); err={429:'rate_limit',500:'server_error',504:'timeout'}[status]
        api_cost = round((inp*0.0010 + out*0.0030)/1000*1400*calls,2) if calls else 0.0

        recontact = 1 if idx in rec_indices else 0
        peer = 1 if idx in peer_indices else 0
        if resolved:
            resolution_type='chatbot'
            feedback=max(1.0,min(5.0,random.gauss(4.1 if period=='month3' else 3.8,0.6)))
        else:
            resolution_type=random.choices(['coworker','department','document','unresolved'],weights=[38,28,14,20])[0]
            feedback=max(1.0,min(5.0,random.gauss(2.3 if period=='initial_1m' else 2.6,0.7)))

        requests.append({
            'request_id':f'R{req_seq:06d}','conversation_id':f'C{conv_seq:05d}','period':period,
            'created_at':created.strftime('%Y-%m-%d %H:%M:%S'),'employee_id':f'E{random.randint(1,300):04d}',
            'employee_department':random.choice(employee_departments),'category':category,'topic':topic,'question_text':question,
            'route':route,'answer_source':answer_source,'knowledge_version':kv,
            'user_confirmed_resolved':resolved,'resolution_type':resolution_type,
            'recontact_within_24h':recontact,'peer_reask':peer,'feedback_score':round(feedback,1),
            'response_seconds':round(resp,2),'input_tokens':inp,'output_tokens':out,
            'api_call_count':calls,'retry_count':retry,'status_code':status,'error_type':err,'api_cost_krw':api_cost
        })
        req_seq += 1
        conv_seq += 1

req_fields=list(requests[0].keys())
with open(DATA/'chatbot_requests.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=req_fields); w.writeheader(); w.writerows(requests)

# KPI summary calculated from the generated raw request data.
# rag_route_rate = share of all requests routed through RAG.
# rag_resolution_rate = success rate within RAG-routed requests.
# direct_llm_route_rate = share handled by direct LLM without RAG.
# llm_call_rate includes RAG + direct LLM because both invoke the model API.
def pct(num, den):
    return round((num / den * 100) if den else 0, 1)

def percentile95(values):
    vals=sorted(values)
    if not vals: return 0
    idx=max(0, math.ceil(0.95*len(vals))-1)
    return round(vals[idx],2)

kpi_header=['period','requests','chatbot_resolution_rate','recontact_rate','peer_reask_rate','faq_hit_rate','rag_route_rate','rag_resolution_rate','direct_llm_route_rate','llm_call_rate','token_per_request','token_per_resolved_request','api_cost_per_request_krw','avg_response_seconds','p95_response_seconds','retry_rate','api_error_rate','avg_feedback_score']
kpi_rows=[]
for period in ['initial_1m','month2','month3']:
    rs=[r for r in requests if r['period']==period]
    n=len(rs)
    resolved=sum(r['user_confirmed_resolved'] for r in rs)
    rag=[r for r in rs if r['route']=='RAG']
    total_tokens=sum(r['input_tokens']+r['output_tokens'] for r in rs)
    api_rows=[r for r in rs if r['api_call_count']>0]
    row=[
        period,n,
        pct(resolved,n),
        pct(sum(r['recontact_within_24h'] for r in rs),n),
        pct(sum(r['peer_reask'] for r in rs),n),
        pct(sum(r['route']=='FAQ' for r in rs),n),
        pct(len(rag),n),
        pct(sum(r['user_confirmed_resolved'] for r in rag),len(rag)),
        pct(sum(r['route']=='LLM' for r in rs),n),
        pct(len(api_rows),n),
        round(total_tokens/n,0),
        round(total_tokens/resolved,0) if resolved else 0,
        round(sum(r['api_cost_krw'] for r in rs)/n,2),
        round(mean(r['response_seconds'] for r in rs),2),
        percentile95([r['response_seconds'] for r in rs]),
        pct(sum(r['retry_count']>0 for r in api_rows),len(api_rows)),
        pct(sum(r['status_code']!=200 for r in api_rows),len(api_rows)),
        round(mean(r['feedback_score'] for r in rs),2),
    ]
    kpi_rows.append(row)
with open(DATA/'kpi_period_summary.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(kpi_header); w.writerows(kpi_rows)

# Sources / benchmark notes
sources = [
    ['source','url','relevance','caveat'],
    ['Moveworks customer story','https://www.moveworks.com/us/en/customers/sustainable-energy-company-ai-powered-employee-support-transformation-with-moveworks','Reports 35% autonomous issue resolution and 40% of all employee support requests resolved in seconds.','Vendor-published case study; timing to reach the metric is not specified.'],
    ['IBM AskIT case study','https://www.ibm.com/case-studies/ibm-transformation/ask-it','IBM built a 90-day MVP for 12,000 users; mature AskIT later reports 86% resolution without human intervention.','86% is a mature-state result, not a 3-month benchmark.'],
]
with open(DATA/'benchmark_sources.csv','w',newline='',encoding='utf-8-sig') as f:
    csv.writer(f).writerows(sources)

print('Generated:')
for p in ['company_profile.csv','baseline_peer_inquiries.csv','baseline_summary.csv','chatbot_requests.csv','kpi_period_summary.csv','benchmark_sources.csv']:
    print(DATA/p)
