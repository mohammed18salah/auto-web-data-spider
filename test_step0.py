import toml

cfg = toml.load('config.toml')
required_sections = ['crawler','nlp','scoring','trusted_domains','domain_scores','export']
for sec in required_sections:
    assert sec in cfg, f'MISSING SECTION: {sec}'
    print(f'  [OK] Config section: [{sec}]')

assert cfg['crawler']['max_depth'] == 3
assert cfg['crawler']['max_sources'] == 200
assert cfg['crawler']['crawl_delay_seconds'] == 2.0
assert 'wikipedia.org' in cfg['domain_scores']
assert cfg['domain_scores']['wikipedia.org'] == 1.0
assert cfg['export']['output_dir'] == './output'
assert len(cfg['trusted_domains']['domains']) == 8

print()
print('=== STEP 0 COMPLETE: All config checks passed! ===')
print('    max_depth =', cfg['crawler']['max_depth'])
print('    max_sources =', cfg['crawler']['max_sources'])
print('    trusted_domains =', cfg['trusted_domains']['domains'])
print('    wikipedia.org score =', cfg['domain_scores']['wikipedia.org'])
