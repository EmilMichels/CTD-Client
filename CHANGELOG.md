# CHANGELOG

<!-- version list -->

## v1.17.0 (2026-05-23)

### Features

- Make dship values accessible from multiprocessing queue
  ([`5e4769c`](https://github.com/DAM-CTD-Software/CTD-Client/commit/5e4769cfd4a3a8dfec4acfa10bfb00b5467d5222))

- Use dship depth value to call plot axis update
  ([`4b5e5e4`](https://github.com/DAM-CTD-Software/CTD-Client/commit/4b5e5e4652766788b021399e4f6ae35f86b01cc1))

- **model**: Adjusting seasave plot axis according to ships echo sounder values
  ([`5f96a47`](https://github.com/DAM-CTD-Software/CTD-Client/commit/5f96a47d63a028e90e145688da3f49f057d67ed8))


## v1.16.0 (2026-05-12)

### Bug Fixes

- Switched lat/lon positioning
  ([`b5846bb`](https://github.com/DAM-CTD-Software/CTD-Client/commit/b5846bbd3723618161da287731d16f542c781f17))

- Update old parameter name in plotting
  ([`76571c0`](https://github.com/DAM-CTD-Software/CTD-Client/commit/76571c0a2f62003b0c14baa18bbce3e7f03267d5))

- Use time filer only in DailyPublications, where time is of interest
  ([`d749f7e`](https://github.com/DAM-CTD-Software/CTD-Client/commit/d749f7eb3854a363e129d7b9ae82872a4e59983e))

### Chores

- Dependency updates
  ([`4d647a0`](https://github.com/DAM-CTD-Software/CTD-Client/commit/4d647a01b79b16ede19dcc3d854525922c4e31ac))

- Do not skip ruff checking of tests anymore
  ([`2c316d1`](https://github.com/DAM-CTD-Software/CTD-Client/commit/2c316d1c8e9764d0b0c889d406c3e3c6f139ff93))

- Removed requirements.txt and its usages
  ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- **deps**: Added myst-parser and click-extra to include markdown readme in docs
  ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

### Code Style

- Initial formatting of test code
  ([`e4141e8`](https://github.com/DAM-CTD-Software/CTD-Client/commit/e4141e82c881a199e8033e2733ce89b00b4edd3b))

### Continuous Integration

- Fix container specification for github actions
  ([#1](https://github.com/DAM-CTD-Software/CTD-Client/pull/1),
  [`12cd780`](https://github.com/DAM-CTD-Software/CTD-Client/commit/12cd7806b5128f39aeea0f42891e69d129490fb3))

- **docs**: Fix path to config ([#3](https://github.com/DAM-CTD-Software/CTD-Client/pull/3),
  [`9a14754`](https://github.com/DAM-CTD-Software/CTD-Client/commit/9a1475471e56787e4801bfc26513f665e9e04379))

### Documentation

- Added github logo to footer and set link information
  ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Added readme badges ([#2](https://github.com/DAM-CTD-Software/CTD-Client/pull/2),
  [`f773b43`](https://github.com/DAM-CTD-Software/CTD-Client/commit/f773b43df7373581ee88e72064d4695f612129c3))

- Added separate usage file for referencing in index
  ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Corrected issues link ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Deleted obsolete files ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Replaced rst index with markdown one ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Replaced rst readme with md one ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Split installing and configuration into two files
  ([#4](https://github.com/DAM-CTD-Software/CTD-Client/pull/4),
  [`0a673a7`](https://github.com/DAM-CTD-Software/CTD-Client/commit/0a673a7374b8426fc4f73139be97bb02d89c595d))

- Udpated docstrings ([#1](https://github.com/DAM-CTD-Software/CTD-Client/pull/1),
  [`12cd780`](https://github.com/DAM-CTD-Software/CTD-Client/commit/12cd7806b5128f39aeea0f42891e69d129490fb3))

### Features

- Force sequential mapping of index to bottle number in Seasave psa
  ([`1768569`](https://github.com/DAM-CTD-Software/CTD-Client/commit/1768569af9f06f7de34131c31a82b8cd27c460e9))

- Using start_position from DataFile which should be in most files
  ([`68e4662`](https://github.com/DAM-CTD-Software/CTD-Client/commit/68e466277643978c238506dba551769a97418f7a))

### Testing

- Fixed template file path ([#1](https://github.com/DAM-CTD-Software/CTD-Client/pull/1),
  [`12cd780`](https://github.com/DAM-CTD-Software/CTD-Client/commit/12cd7806b5128f39aeea0f42891e69d129490fb3))

- Update nrt tests according to code changes
  ([`c011849`](https://github.com/DAM-CTD-Software/CTD-Client/commit/c011849100ae2722c21555fca9417389f5f1ef90))


## v1.15.0 (2026-03-31)

- last release on [institutional gitea instance](https://git.iow.de/CTD-Software/CTD-Client) prior to moving to GitHub.

- for details, check MIGRATION.md
