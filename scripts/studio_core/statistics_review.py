"""Optional, source-bound meaning for a reported mean ± dispersion.

Never infer SD/SE from its magnitude. Existing runs without this extension retain
their contract. Descriptive CSV arithmetic is not an ecological model replication.
"""
import csv,math,re,statistics
from decimal import Decimal
from pathlib import Path
from .common import require,sha

def statistic_definitions(job,analysis,review):
    definitions=analysis.get('statisticalDefinitions',[])
    require(isinstance(definitions,list),'STATISTIC_DEFINITION','Statistic definitions must be a list.')
    ids=[d.get('id') for d in definitions]
    require(len(set(ids))==len(ids),'STATISTIC_DEFINITION','Duplicate statistic definition.')
    claims={c['id']:c for c in analysis['claims']};evidence={e['id']:e for e in analysis['evidence']}
    assessments={x.get('id'):x for x in review.get('statisticalDefinitions',[])}
    for d in definitions:
        require(d.get('claimId') in claims and d.get('kind') in ('mean-sd','mean-se','reported-unknown') and d.get('comparison') and d.get('unit'),'STATISTIC_DEFINITION','Declare comparison, unit, claim and dispersion meaning.')
        qs=claims[d['claimId']].get('quantities',[]);indices=d.get('quantityIndices',[])
        require(len(indices)==2 and len(set(indices))==2 and all(type(i)is int and 0<=i<len(qs) for i in indices),'STATISTIC_DEFINITION','Map distinct reported mean and dispersion quantities.')
        mean,disp=[float(qs[i]['value']) for i in indices]
        require(math.isfinite(mean) and math.isfinite(disp) and disp>=0 and all(qs[i]['unit']==d['unit'] for i in indices),'STATISTIC_UNIT','Summary mean and dispersion must retain their source unit.')
        a=assessments.get(d['id'],{})
        require(a.get('status')=='verified' and a.get('rationale'),'STATISTIC_REVIEW','Review the meaning, not just numeric presence.')
        basis=d.get('basis',{});method=basis.get('method')
        if method=='explicit-source-definition':
            e=evidence.get(basis.get('evidenceId'),{});text=e.get('quote','')
            pattern=r'\bS\.?\s*D\.?(?![A-Za-z])|standard deviation|标准差' if d['kind']=='mean-sd' else r'\bS\.?\s*E\.?(?![A-Za-z])|standard error|标准误'
            require(d['kind']!='reported-unknown' and e.get('id') in claims[d['claimId']]['evidenceIds'] and re.search(pattern,text,re.I),'STATISTIC_BASIS','An explicit definition must actually name this dispersion in cited evidence.')
        elif method=='checked-csv-recalculation':
            require(d['kind']=='mean-sd','STATISTIC_BASIS','This adapter verifies descriptive sample SD only; it does not derive inferential intervals or relabel a reported SE.')
            root=Path(job).resolve();p=(root/basis.get('path','')).resolve()
            require(p.is_relative_to(root) and p.is_file() and sha(p)==basis.get('sha256'),'STATISTIC_SOURCE','Supporting data snapshot is absent, outside the run, or changed.')
            require(basis.get('sourceUrl') and basis.get('sourceMember') and basis.get('rationale'),'STATISTIC_SOURCE','Record the primary download, member and semantic correspondence.')
            with p.open(encoding='utf-8-sig',newline='') as stream:
                rows=list(csv.DictReader(stream))
            try:
                values=[float(r[basis['differenceColumn']]) for r in rows]
                valid=all(math.isfinite(v) and abs(v-(float(r[basis['afterColumn']])-float(r[basis['beforeColumn']])))<1e-9 for v,r in zip(values,rows))
            except (ValueError,KeyError,TypeError):values=[];valid=False
            require(valid and len(values)>=2 and len(values)==basis.get('rows'),'STATISTIC_ARITHMETIC','Check each supplied difference and its rows, not a screenshot estimate.')
            digits=d.get('reportedDecimals')
            require(type(digits)is int and 0<=digits<=10,'STATISTIC_PRECISION','Declare the reported decimal precision.')
            matches=lambda x,y:round(Decimal(str(x)),digits)==round(Decimal(str(y)),digits)
            require(matches(statistics.mean(values),mean) and matches(statistics.stdev(values),disp),'STATISTIC_ARITHMETIC','Public data mean/sample SD do not reproduce the reported pair at its precision.')
        else:
            require(method=='unresolved-definition' and d['kind']=='reported-unknown' and basis.get('rationale'),'STATISTIC_BASIS','Unresolved dispersion must remain explicitly unresolved.')
    return {d['id']:d for d in definitions}

def validate_summary(slide,claims,definitions):
    block=slide.get('visual',{}).get('reportedStatistic')
    if not block:return
    d=definitions.get(block.get('definitionId'),{})
    require(d and d['claimId'] in slide.get('claimIds',[]),'STATISTIC_SUMMARY_SOURCE','Summary must cite a verified current-paper definition.')
    text=slide['visual'].get('text',{});value=text.get('summaryValue','');label=text.get('summaryDefinition','')
    from .contracts import numbers
    qs=claims[d['claimId']]['quantities'];expected=set().union(*(numbers(qs[i]['value']) for i in d['quantityIndices']))
    require(numbers(value)==expected and '±' in value,'STATISTIC_SUMMARY_VALUE','Display the reported pair unchanged, with its dispersion.')
    pattern={'mean-sd':r'\bSD\b|标准差','mean-se':r'\bSE\b|标准误','reported-unknown':r'未明确|未定义|unknown|unspecified'}[d['kind']]
    require(label and re.search(pattern,label,re.I) and not re.search(r'\bCI\b|置信区间|credible|prediction interval',label,re.I),'STATISTIC_SUMMARY_LABEL','Name the verified dispersion; an SD/SE is not a confidence interval.')
