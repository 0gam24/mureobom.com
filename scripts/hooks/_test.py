"""훅 단위 테스트. 통과 시 ALL PASS 출력.
실행: PYTHONIOENCODING=utf-8 python -X utf8 scripts/hooks/_test.py
"""
import json, subprocess, sys

cases = [
    ('meta CLAUDE.md - allow',
     {'tool_name':'Write','tool_input':{'file_path':'CLAUDE.md','content':'지식iN 데이터'}}, 0),
    ('agent def - allow',
     {'tool_name':'Write','tool_input':{'file_path':'.claude/agents/researcher.md','content':'지식iN 차단'}}, 0),
    ('src/content/answers w/ kin URL - BLOCK',
     {'tool_name':'Write','tool_input':{'file_path':'src/content/answers/x.md','content':'https://kin.naver.com/qna/d.nhn'}}, 2),
    ('automation brief.yaml jisikiN - BLOCK',
     {'tool_name':'Write','tool_input':{'file_path':'automation/briefs/tax/foo.brief.yaml','content':'human_notes: 지식iN'}}, 2),
    ('automation example.brief.yaml jisikiN - allow (meta)',
     {'tool_name':'Write','tool_input':{'file_path':'automation/briefs/example.brief.yaml','content':'지식iN'}}, 0),
    ('automation _schema.md jisikiN - allow (meta)',
     {'tool_name':'Write','tool_input':{'file_path':'automation/briefs/_schema.md','content':'지식iN'}}, 0),
    ('src/content/answers w/ blog.naver - BLOCK',
     {'tool_name':'Edit','tool_input':{'file_path':'src/content/answers/x.md','new_string':'https://blog.naver.com/foo'}}, 2),
    ('public/llms.txt clean - allow',
     {'tool_name':'Write','tool_input':{'file_path':'public/llms.txt','content':'- /tax/x clean'}}, 0),
    ('public/llms.txt jisikiN - BLOCK',
     {'tool_name':'Write','tool_input':{'file_path':'public/llms.txt','content':'지식iN'}}, 2),
    ('src/content/answers clean - allow',
     {'tool_name':'Write','tool_input':{'file_path':'src/content/answers/x.md','content':'고용보험법 제40조'}}, 0),
    ('README kin URL - allow (non-protected)',
     {'tool_name':'Write','tool_input':{'file_path':'README.md','content':'https://kin.naver.com'}}, 0),
    ('windows backslash answers - BLOCK',
     {'tool_name':'Write','tool_input':{'file_path':'src\\content\\answers\\x.md','content':'https://kin.naver.com'}}, 2),
    ('cafe.naver in brief - BLOCK',
     {'tool_name':'Write','tool_input':{'file_path':'automation/briefs/tax/foo.brief.yaml','content':'https://cafe.naver.com/x'}}, 2),
    ('Read tool - allow (not Write/Edit)',
     {'tool_name':'Read','tool_input':{'file_path':'src/content/answers/x.md'}}, 0),
    ('src/layouts/ Astro file - allow (not protected)',
     {'tool_name':'Edit','tool_input':{'file_path':'src/layouts/Base.astro','new_string':'<!-- 지식iN 참고 -->'}}, 0),
]

all_ok = True
for label, payload, expected in cases:
    p = subprocess.run(
        [sys.executable, 'scripts/hooks/no_kin_originals.py'],
        input=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        capture_output=True
    )
    ok = p.returncode == expected
    all_ok &= ok
    mark = 'PASS' if ok else 'FAIL'
    print(f'{mark}  exit={p.returncode} expect={expected} :: {label}')
    if not ok and p.stderr:
        print('  stderr:', p.stderr.decode(errors='replace')[:200])

print('---')
print('ALL PASS' if all_ok else 'SOME FAILED')
sys.exit(0 if all_ok else 1)
