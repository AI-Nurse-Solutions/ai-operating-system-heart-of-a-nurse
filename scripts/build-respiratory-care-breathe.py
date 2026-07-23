#!/usr/bin/env python3
"""Build the standalone, deterministic BREATHE Respiratory Care release.

This script packages files only. It never installs BREATHE, modifies a Hermes
profile, enables memory, connects an account or device, schedules work, runs an
agent, or performs a clinical, device, or external action.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "respiratory-care"
PACKAGE = ROOT / "packages" / "breathe"
DOWNLOADS = ROOT / "downloads"
BUILD_KIT_SOURCE = ROOT / "build-kit"
ZIP_NAME = "breathe-respiratory-care-complete-edition.zip"
ZIP_PREFIX = "BREATHE-Respiratory-Care-Complete-Edition"
BUILD_KIT_NAME = "BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_SHA256 = "8fe551cd982d8ab8d33c3bd23b8365b45f7f8e714c80b326bf54e075b21c3a7d"
BUILD_KIT_BYTES = 6966334
BUILD_KIT_MEMBERS = 151
BUILD_KIT_ROOT = "BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0"
BUILD_KIT_VERIFIER_SHA256 = "9dc166dabb30aefe8bc6f5bf9e1dc83cdf631182acd8491355af3cb49b3de041"
BUILD_KIT_MAX_MEMBER_BYTES = 32 * 1024 * 1024
BUILD_KIT_MAX_EXPANDED_BYTES = 192 * 1024 * 1024
BUILD_KIT_ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
BUILD_KIT_EXECUTABLE_MEMBERS = {
    f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py",
}
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)
SOURCE_RECORDS = {'README.md': {'bytes': 6744,
               'packaged_path': 'README.md',
               'source_sha256': 'b85901213e49c5f44be866ceb63f662d2206b6028b4f4d0f8b2f69ab5a994601',
               'transformation': 'corrected the two supplied SHA256SUMS.txt references to the published '
                                 'PACKAGE-CHECKSUMS.sha256 and renamed UPSTREAM-SHA256SUMS.txt paths, adding the '
                                 'provenance-mapping instruction; all other text and order are unchanged',
               'upstream_bytes': 6446,
               'upstream_path': 'README.md',
               'upstream_sha256': 'b10de0f4f3cdb6ffcb33f09a90440b92c3bd3732f905fcbd68907d3e54f4eadf'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/README.md': {'bytes': 681,
                                                              'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/README.md',
                                                              'source_sha256': 'c48395a08ee00237fed7792d2f0d1cd7a67d3fa900b51c3f4c579ba6c6aa32c5',
                                                              'transformation': 'replaced supplied Markdown '
                                                                                'trailing-space hard breaks with '
                                                                                'explicit <br> tags for semantic '
                                                                                'rendering and a whitespace-clean '
                                                                                'repository without changing text or '
                                                                                'order',
                                                              'upstream_bytes': 679,
                                                              'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/README.md',
                                                              'upstream_sha256': 'cef7aaac31e22bb68f969f13d283d28cea9815e843fb9c986e43da1282667a7d'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/01-B-Begin-Safely.md': {'bytes': 11040,
                                                                                 'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/01-B-Begin-Safely.md',
                                                                                 'source_sha256': '50ffebaf7e5a20e2c0cf38a35f4e6c76402cb64589e5735a8265ea521fd1b263',
                                                                                 'transformation': 'none; '
                                                                                                   'byte-for-byte copy '
                                                                                                   'from the supplied '
                                                                                                   'archive',
                                                                                 'upstream_bytes': 11040,
                                                                                 'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/01-B-Begin-Safely.md',
                                                                                 'upstream_sha256': '50ffebaf7e5a20e2c0cf38a35f4e6c76402cb64589e5735a8265ea521fd1b263'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/02-R-Reason-with-Evidence.md': {'bytes': 10875,
                                                                                         'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/02-R-Reason-with-Evidence.md',
                                                                                         'source_sha256': '824bb6b2b6e3dd65b95c8efa8152104db9ad35405b705d05483f63260ca9af9b',
                                                                                         'transformation': 'none; '
                                                                                                           'byte-for-byte '
                                                                                                           'copy from '
                                                                                                           'the '
                                                                                                           'supplied '
                                                                                                           'archive',
                                                                                         'upstream_bytes': 10875,
                                                                                         'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/02-R-Reason-with-Evidence.md',
                                                                                         'upstream_sha256': '824bb6b2b6e3dd65b95c8efa8152104db9ad35405b705d05483f63260ca9af9b'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/03-E-Equip-for-Reliability.md': {'bytes': 11081,
                                                                                          'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/03-E-Equip-for-Reliability.md',
                                                                                          'source_sha256': 'f70a5e0754b54677a64802400d67d084e011699bae192899d2f75ea6ced35c7c',
                                                                                          'transformation': 'none; '
                                                                                                            'byte-for-byte '
                                                                                                            'copy from '
                                                                                                            'the '
                                                                                                            'supplied '
                                                                                                            'archive',
                                                                                          'upstream_bytes': 11081,
                                                                                          'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/03-E-Equip-for-Reliability.md',
                                                                                          'upstream_sha256': 'f70a5e0754b54677a64802400d67d084e011699bae192899d2f75ea6ced35c7c'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/04-A-Align-Airway-and-Teams.md': {'bytes': 11079,
                                                                                           'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/04-A-Align-Airway-and-Teams.md',
                                                                                           'source_sha256': 'd985c3aedcbee48f3e5948a752e3a6c58a772cb15566c4060bf0f355c50affc6',
                                                                                           'transformation': 'none; '
                                                                                                             'byte-for-byte '
                                                                                                             'copy '
                                                                                                             'from the '
                                                                                                             'supplied '
                                                                                                             'archive',
                                                                                           'upstream_bytes': 11079,
                                                                                           'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/04-A-Align-Airway-and-Teams.md',
                                                                                           'upstream_sha256': 'd985c3aedcbee48f3e5948a752e3a6c58a772cb15566c4060bf0f355c50affc6'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/05-T-Teach-Improve-and-Advance.md': {'bytes': 8446,
                                                                                              'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/05-T-Teach-Improve-and-Advance.md',
                                                                                              'source_sha256': 'ba74ec35f32ec6293a680a12c48d1a7fa3f498ff01bc91408c778d601168e49c',
                                                                                              'transformation': 'none; '
                                                                                                                'byte-for-byte '
                                                                                                                'copy '
                                                                                                                'from '
                                                                                                                'the '
                                                                                                                'supplied '
                                                                                                                'archive',
                                                                                              'upstream_bytes': 8446,
                                                                                              'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/05-T-Teach-Improve-and-Advance.md',
                                                                                              'upstream_sha256': 'ba74ec35f32ec6293a680a12c48d1a7fa3f498ff01bc91408c778d601168e49c'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/06-H-Honor-Humans-and-Future.md': {'bytes': 5642,
                                                                                            'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/06-H-Honor-Humans-and-Future.md',
                                                                                            'source_sha256': 'bed6449a78f977a127cb7ffd5e13aac087aa40365eeeb5a74b4af6dbe3b16d8b',
                                                                                            'transformation': 'none; '
                                                                                                              'byte-for-byte '
                                                                                                              'copy '
                                                                                                              'from '
                                                                                                              'the '
                                                                                                              'supplied '
                                                                                                              'archive',
                                                                                            'upstream_bytes': 5642,
                                                                                            'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/06-H-Honor-Humans-and-Future.md',
                                                                                            'upstream_sha256': 'bed6449a78f977a127cb7ffd5e13aac087aa40365eeeb5a74b4af6dbe3b16d8b'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/07-E-Engineer-Ethical-Agents.md': {'bytes': 8622,
                                                                                            'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/07-E-Engineer-Ethical-Agents.md',
                                                                                            'source_sha256': '67bd68067c8cfe588d1d686eb62597dddc9987112f6c86a279ed1c06bea8456b',
                                                                                            'transformation': 'added an explicit TPL-28 multi-agent output mapping; all other text and order are unchanged',
                                                                                            'upstream_bytes': 8492,
                                                                                            'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/breathe/07-E-Engineer-Ethical-Agents.md',
                                                                                            'upstream_sha256': 'dcfd343b737e638991fedea5d5098a49579b9c61a2c1ab534e4420eb80dde4a9'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/00-Standalone-Respiratory-Care-Lane-and-Human-Standard.md': {'bytes': 2933,
                                                                                                                   'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/00-Standalone-Respiratory-Care-Lane-and-Human-Standard.md',
                                                                                                                   'source_sha256': 'bda57fa13d693b0848ec769418706eca7c044b1ed4117de11e963c70276fb53f',
                                                                                                                   'transformation': 'corrected powers 22–24 to Available Inactive while associated suggested agents remain PERM-P0 Disabled; all other text and order are unchanged',
                                                                                                                   'upstream_bytes': 2892,
                                                                                                                   'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/00-Standalone-Respiratory-Care-Lane-and-Human-Standard.md',
                                                                                                                   'upstream_sha256': '37acb1fa00c0b916594e28ea80d3786ffc666d83859954699461ad3bb4a11950'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/01-Respiratory-Professional-Patient-Team-Device-and-Institution-Trust-Shield.md': {'bytes': 2850,
                                                                                                                                         'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/01-Respiratory-Professional-Patient-Team-Device-and-Institution-Trust-Shield.md',
                                                                                                                                         'source_sha256': '4f2dbc27c328e4edcf639ae420feb6e812703a2fd141c509b1ceb412c71eee24',
                                                                                                                                         'transformation': 'none; '
                                                                                                                                                           'byte-for-byte '
                                                                                                                                                           'copy '
                                                                                                                                                           'from '
                                                                                                                                                           'the '
                                                                                                                                                           'supplied '
                                                                                                                                                           'archive',
                                                                                                                                         'upstream_bytes': 2850,
                                                                                                                                         'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/01-Respiratory-Professional-Patient-Team-Device-and-Institution-Trust-Shield.md',
                                                                                                                                         'upstream_sha256': '4f2dbc27c328e4edcf639ae420feb6e812703a2fd141c509b1ceb412c71eee24'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/02-BREATHE-SCOPE-CIRCLE-ORBIT-Operating-Core.md': {'bytes': 4664,
                                                                                                         'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/02-BREATHE-SCOPE-CIRCLE-ORBIT-Operating-Core.md',
                                                                                                         'source_sha256': '6de2bd6ddc3926ba022fa991e16e8a5e5cc48bbf9da6c9bdd212926758e0e209',
                                                                                                         'transformation': 'none; '
                                                                                                                           'byte-for-byte '
                                                                                                                           'copy '
                                                                                                                           'from '
                                                                                                                           'the '
                                                                                                                           'supplied '
                                                                                                                           'archive',
                                                                                                         'upstream_bytes': 4664,
                                                                                                         'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/core/02-BREATHE-SCOPE-CIRCLE-ORBIT-Operating-Core.md',
                                                                                                         'upstream_sha256': '6de2bd6ddc3926ba022fa991e16e8a5e5cc48bbf9da6c9bdd212926758e0e209'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/foundation/Respiratory-Care-Life-Practice-and-Professional-Foundation.md': {'bytes': 15014,
                                                                                                                             'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/foundation/Respiratory-Care-Life-Practice-and-Professional-Foundation.md',
                                                                                                                             'source_sha256': 'd7b047d2f76dbd29c6bbc616d7919bb7edb3af994662576a4273881e6ad2a57a',
                                                                                                                             'transformation': 'none; '
                                                                                                                                               'byte-for-byte '
                                                                                                                                               'copy '
                                                                                                                                               'from '
                                                                                                                                               'the '
                                                                                                                                               'supplied '
                                                                                                                                               'archive',
                                                                                                                             'upstream_bytes': 15014,
                                                                                                                             'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/foundation/Respiratory-Care-Life-Practice-and-Professional-Foundation.md',
                                                                                                                             'upstream_sha256': 'd7b047d2f76dbd29c6bbc616d7919bb7edb3af994662576a4273881e6ad2a57a'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/manifest.md': {'bytes': 4682,
                                                                'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/manifest.md',
                                                                'source_sha256': '38c3ac56d9933bdcfe4c64e2380f279d130d0313352f5baafb59f95d429984f6',
                                                                'transformation': 'replaced supplied Markdown '
                                                                                  'trailing-space hard breaks with '
                                                                                  'explicit <br> tags for semantic '
                                                                                  'rendering and a whitespace-clean '
                                                                                  'repository without changing text or '
                                                                                  'order',
                                                                'upstream_bytes': 4664,
                                                                'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/manifest.md',
                                                                'upstream_sha256': '0faedbc17d49d71ee1097bebb8e011569ed98115253f4fc26cd050ef87f6b893'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/templates/BREATHE-Cards-and-Templates.md': {'bytes': 44257,
                                                                                             'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/templates/BREATHE-Cards-and-Templates.md',
                                                                                             'source_sha256': '1247d453f12258c888318e3589538c6abf1ae18d3ded992069d422f48ff97cb6',
                                                                                             'transformation': 'replaced supplied Markdown trailing-space hard breaks with explicit <br> tags; removed the undefined emergency-bypass gate state; aligned all common headers; and made TPL-28 represent multi-agent sequences, permissions, transfers, disagreements, human reviews, failures and termination evidence; all other text and order are unchanged',
                                                                                             'upstream_bytes': 42009,
                                                                                             'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/templates/BREATHE-Cards-and-Templates.md',
                                                                                             'upstream_sha256': 'c51891e757f190cf7bdf07d92633d1373dd798ee5df70fc86a868d5d44befa81'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/tests/BREATHE-Release-Assurance.md': {'bytes': 55452,
                                                                                       'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/tests/BREATHE-Release-Assurance.md',
                                                                                       'source_sha256': '5fe51985df8345c859f5d394448b5e87419a63048515002580ba410b046d1c04',
                                                                                       'transformation': 'none; '
                                                                                                         'byte-for-byte '
                                                                                                         'copy from '
                                                                                                         'the supplied '
                                                                                                         'archive',
                                                                                       'upstream_bytes': 55452,
                                                                                       'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/tests/BREATHE-Release-Assurance.md',
                                                                                       'upstream_sha256': '5fe51985df8345c859f5d394448b5e87419a63048515002580ba410b046d1c04'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/BREATHE-Workflows-Launch-and-Adoption-Plan.md': {'bytes': 58691,
                                                                                                            'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/BREATHE-Workflows-Launch-and-Adoption-Plan.md',
                                                                                                            'source_sha256': 'e638979452fcae6698dbb34a32e195c1355de60063cb90b06d9e42ec4eb15e18',
                                                                                                            'transformation': "replaced supplied Markdown trailing-space hard breaks with explicit <br> tags; isolated WF-04 whole-life data; added approver evidence to all receipts; removed WF-22's duplicate ORBIT attachment; and mapped WF-23 to the representable TPL-28 sequence contract; all other text and order are unchanged",
                                                                                                            'upstream_bytes': 55531,
                                                                                                            'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/BREATHE-Workflows-Launch-and-Adoption-Plan.md',
                                                                                                            'upstream_sha256': '4b5bb85caba0bee2aeeb23e0f8a5a7870c3ad5b1f1c0c28fb6e16b0e92b4316f'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/My-BREATHE-Respiratory-Care-Command-Center.md': {'bytes': 2874,
                                                                                                            'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/My-BREATHE-Respiratory-Care-Command-Center.md',
                                                                                                            'source_sha256': '78a8ad74623a7d4f0b3fbeb50a10b8de1d62320e1637a072a52d0626b224a37c',
                                                                                                            'transformation': 'replaced '
                                                                                                                              'supplied '
                                                                                                                              'Markdown '
                                                                                                                              'trailing-space '
                                                                                                                              'hard '
                                                                                                                              'breaks '
                                                                                                                              'with '
                                                                                                                              'explicit '
                                                                                                                              '<br> '
                                                                                                                              'tags '
                                                                                                                              'for '
                                                                                                                              'semantic '
                                                                                                                              'rendering '
                                                                                                                              'and '
                                                                                                                              'a '
                                                                                                                              'whitespace-clean '
                                                                                                                              'repository '
                                                                                                                              'without '
                                                                                                                              'changing '
                                                                                                                              'text '
                                                                                                                              'or '
                                                                                                                              'order',
                                                                                                            'upstream_bytes': 2870,
                                                                                                            'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/My-BREATHE-Respiratory-Care-Command-Center.md',
                                                                                                            'upstream_sha256': '332f1041e1ff9a84c21686fcdc5f055c4cf35e86b7b2ffd9401057fc3648be1e'},
 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/Respiratory-Role-Setting-and-Situation-Recipes.md': {'bytes': 2573,
                                                                                                                'packaged_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/Respiratory-Role-Setting-and-Situation-Recipes.md',
                                                                                                                'source_sha256': '6aecee0f209c555719684aeea49439aff25ffbdec0c7b101ed176c4e438dc9f5',
                                                                                                                'transformation': 'none; '
                                                                                                                                  'byte-for-byte '
                                                                                                                                  'copy '
                                                                                                                                  'from '
                                                                                                                                  'the '
                                                                                                                                  'supplied '
                                                                                                                                  'archive',
                                                                                                                'upstream_bytes': 2573,
                                                                                                                'upstream_path': 'Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/workflows/Respiratory-Role-Setting-and-Situation-Recipes.md',
                                                                                                                'upstream_sha256': '6aecee0f209c555719684aeea49439aff25ffbdec0c7b101ed176c4e438dc9f5'},
 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md': {'bytes': 273780,
                                                                                'packaged_path': 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md',
                                                                                'source_sha256': '0250340ba2b1603d84c56603f7271ac6531e20cb6979bc2a0e25d62ab896406a',
                                                                                'transformation': 'replaced supplied Markdown trailing-space hard breaks with explicit <br> tags; bound Activation Card approval to the exact complete-program digest; removed the undefined emergency-bypass gate state; and synchronized the reviewed power-state, whole-life isolation, approval-receipt, ORBIT and representable multi-agent contracts; all other text and order are unchanged',
                                                                                'upstream_bytes': 267975,
                                                                                'upstream_path': 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md',
                                                                                'upstream_sha256': '63821c41bd20b34edd7245d2eb640d695b7a80b33e0586893a8387e444d813bb'},
 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx': {'bytes': 194330,
                                                                               'packaged_path': 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx',
                                                                               'source_sha256': 'd2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc',
                                                                               'transformation': 'none; byte-for-byte '
                                                                                                 'copy from the '
                                                                                                 'supplied archive',
                                                                               'upstream_bytes': 194330,
                                                                               'upstream_path': 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx',
                                                                               'upstream_sha256': 'd2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc'},
 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md': {'bytes': 20238,
                                                                             'packaged_path': 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md',
                                                                             'source_sha256': 'f80690b24eacbe2b2724119107be78e887b166115ea95ebdef19f84e3ec33cbd',
                                                                             'transformation': 'replaced supplied '
                                                                                               'Markdown '
                                                                                               'trailing-space hard '
                                                                                               'breaks with explicit '
                                                                                               '<br> tags for semantic '
                                                                                               'rendering and a '
                                                                                               'whitespace-clean '
                                                                                               'repository without '
                                                                                               'changing text or order',
                                                                             'upstream_bytes': 20220,
                                                                             'upstream_path': 'Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md',
                                                                             'upstream_sha256': '1ff712f65a167c812b66e32cfa4d588be247617506640772da349592c2e988ff'},
 'UPSTREAM-SHA256SUMS.txt': {'bytes': 3338,
                             'packaged_path': 'UPSTREAM-SHA256SUMS.txt',
                             'source_sha256': '9a3cfe815619a97907407bfeb3744ab5ea6c8da22eca2ebffddfaf409fa63f20',
                             'transformation': 'renamed from SHA256SUMS.txt to distinguish the supplied '
                                               'pre-normalization provenance ledger from PACKAGE-CHECKSUMS.sha256',
                             'upstream_bytes': 3338,
                             'upstream_path': 'SHA256SUMS.txt',
                             'upstream_sha256': '9a3cfe815619a97907407bfeb3744ab5ea6c8da22eca2ebffddfaf409fa63f20'}}
WRAPPER_DIGESTS = {
    "00-READ-FIRST.md": "cfe95016b123c144d97429d27a30a2e2e602e5417c5370965f8df52a9c80e2a2",
    "ROLE-PACK.json": "abf96a4aaf177a41b14bb453aa783910449f51b4f4a0d2f6300c9ace9ae30858",
}
EXPECTED_FILES = set(SOURCE_RECORDS) | set(WRAPPER_DIGESTS) | {"PACKAGE-CHECKSUMS.sha256"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in PACKAGE.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"BREATHE package symlink is forbidden: {path.relative_to(PACKAGE)}")
        if path.is_file():
            files[path.relative_to(PACKAGE).as_posix()] = path
    return files


def load_manifest() -> dict:
    manifest = json.loads((PACKAGE / "ROLE-PACK.json").read_text(encoding="utf-8"))
    expected = {
        "acceptance_tests": {"breathe_overlay": 72, "foundation": 72, "integration": 16, "total": 160},
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "namespace": "resp_breathe.*",
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 24,
        "package_version": "2026.07.16.1",
        "population_lane": "respiratory_care",
        "program_id": "RCAIOS-BREATHE-COMPLETE-1.0",
        "records_total": 18,
        "respiratory_home": "My BREATHE",
        "route": "/respiratory-care/",
        "suggested_agents_active_after_install": 0,
        "suggested_agents_total": 10,
        "templates_total": 30,
        "workflows_total": 24,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"BREATHE manifest mismatch for {key}")
    true_keys = (
        "breathe_overlay_second", "foundation_first", "institutional_deployment_requires_separate_authorization",
        "no_phi", "pre_install_disclosure_required", "standalone_non_nurse_lane",
    )
    false_keys = (
        "automatic_connectors", "automatic_cron", "automatic_device_access", "automatic_external_actions",
        "automatic_memory", "automatic_shared_access", "clinical_decisions", "device_control",
        "device_data_private_use", "install_on_download", "live_patient_specific_private_use",
        "medical_resident_population_state_shared", "nursing_population_state_shared",
        "role_selection_verifies_credentials_or_authority",
    )
    for key in true_keys:
        if manifest.get(key) is not True:
            raise ValueError(f"BREATHE safety flag must be true: {key}")
    for key in false_keys:
        if manifest.get(key) is not False:
            raise ValueError(f"BREATHE safety flag must be false: {key}")
    archive = manifest.get("source_archive", {})
    if archive != {
        "bytes": 317428,
        "members": 23,
        "sha256": "7fc1d4b0a8dec362bcd41e5e049b1498d70fc2cbfd9d0348f5d7b240172f2edb",
        "supplied_name": "BREATHE-Respiratory-Care-Pack.zip",
    }:
        raise ValueError("BREATHE source archive provenance changed")
    declared = {item.get("packaged_path"): item for item in manifest.get("source_files", [])}
    if declared != SOURCE_RECORDS:
        raise ValueError("BREATHE source inventory, digest, bytes, or transformation declarations changed")
    return manifest


def parse_ledger(name: str, expected: set[str]) -> dict[str, str]:
    records: dict[str, str] = {}
    ledger = PACKAGE / name
    for line_number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"Malformed BREATHE checksum line {line_number} in {name}")
        relative = Path(match.group(2))
        if "\\" in match.group(2) or relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"Unsafe BREATHE checksum path: {relative}")
        path_name = relative.as_posix()
        if path_name in records:
            raise ValueError(f"Duplicate BREATHE checksum path: {path_name}")
        records[path_name] = match.group(1)
    if set(records) != expected:
        raise ValueError(f"BREATHE checksum ledger inventory mismatch in {name}")
    return records


def validate_upstream_ledger() -> None:
    expected = {record["upstream_path"] for record in SOURCE_RECORDS.values() if record["upstream_path"] != "SHA256SUMS.txt"}
    records = parse_ledger("UPSTREAM-SHA256SUMS.txt", expected)
    declared = {record["upstream_path"]: record["upstream_sha256"] for record in SOURCE_RECORDS.values() if record["upstream_path"] != "SHA256SUMS.txt"}
    if records != declared:
        raise ValueError("BREATHE supplied upstream checksum ledger does not match pinned provenance")


def validate_embedded_parity() -> None:
    program_name = "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md"
    program = (PACKAGE / program_name).read_text(encoding="utf-8")
    markers = re.findall(r"^<!-- BEGIN EMBEDDED COMPONENT: (.+) -->$", program, re.MULTILINE)
    if len(markers) != 17 or len(set(markers)) != 17:
        raise ValueError("BREATHE embedded component inventory mismatch")
    source_root = PACKAGE / "Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0"
    for relative in markers:
        if relative.startswith(("/", "\\")) or ".." in Path(relative).parts or "\\" in relative:
            raise ValueError(f"Unsafe BREATHE embedded component path: {relative}")
        start = f"<!-- BEGIN EMBEDDED COMPONENT: {relative} -->"
        end = f"<!-- END EMBEDDED COMPONENT: {relative} -->"
        segment = program.split(start, 1)[1].split(end, 1)[0].strip("\n")
        source = (source_root / relative).read_text(encoding="utf-8").strip("\n")
        if segment != source:
            raise ValueError(f"BREATHE embedded/source parity mismatch: {relative}")


def validate_package() -> dict:
    if not PACKAGE.is_dir():
        raise FileNotFoundError(PACKAGE)
    files = package_files()
    if set(files) != EXPECTED_FILES:
        raise ValueError(f"BREATHE package inventory mismatch: {sorted(files)}")
    for name, record in SOURCE_RECORDS.items():
        path = PACKAGE / name
        if path.stat().st_size != record["bytes"] or sha256(path) != record["source_sha256"]:
            raise ValueError(f"Trusted BREATHE source digest or byte mismatch: {name}")
    for name, digest in WRAPPER_DIGESTS.items():
        if sha256(PACKAGE / name) != digest:
            raise ValueError(f"Trusted BREATHE wrapper digest mismatch: {name}")
    manifest = load_manifest()
    validate_upstream_ledger()
    validate_embedded_parity()
    ledger = parse_ledger("PACKAGE-CHECKSUMS.sha256", EXPECTED_FILES - {"PACKAGE-CHECKSUMS.sha256"})
    for name, digest in ledger.items():
        if sha256(PACKAGE / name) != digest:
            raise ValueError(f"BREATHE package checksum mismatch: {name}")
    return manifest


def refresh_ledger() -> None:
    targets = [PACKAGE / name for name in sorted(EXPECTED_FILES - {"PACKAGE-CHECKSUMS.sha256"})]
    content = "\n".join(f"{sha256(path)}  {path.relative_to(PACKAGE).as_posix()}" for path in targets) + "\n"
    (PACKAGE / "PACKAGE-CHECKSUMS.sha256").write_text(content, encoding="utf-8")


def _safe_build_kit_member(name: str, root: Path | None = None) -> Path | None:
    """Reject every noncanonical archive spelling before payload access."""
    if not name or "\x00" in name or "\\" in name:
        raise ValueError(f"Unsafe BREATHE build-kit member path: {name!r}")
    relative = PurePosixPath(name)
    canonical = relative.as_posix() + ("/" if name.endswith("/") else "")
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or any(part in {"", ".", ".."} or ":" in part for part in relative.parts)
        or name != canonical
    ):
        raise ValueError(f"Unsafe BREATHE build-kit member path: {name!r}")
    if root is None:
        return None
    resolved_root = root.resolve()
    target = root.joinpath(*relative.parts).resolve()
    if not str(target).startswith(str(resolved_root) + os.sep):
        raise ValueError(f"BREATHE build-kit member escapes verification root: {name!r}")
    return target


def build_kit_source_files() -> list[Path]:
    source = BUILD_KIT_SOURCE / BUILD_KIT_ROOT
    if not source.is_dir():
        raise ValueError(f"Missing tracked BREATHE build-kit source tree: {source}")
    files = sorted(path for path in source.rglob("*") if path.is_file())
    if len(files) != BUILD_KIT_MEMBERS:
        raise ValueError(f"BREATHE tracked build-kit source inventory changed: {len(files)}")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("BREATHE tracked build-kit source tree must not contain symlinks")
    return files


def _write_build_kit_zip(output: Path) -> None:
    files = build_kit_source_files()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(BUILD_KIT_SOURCE / BUILD_KIT_ROOT).as_posix()
            member = f"{BUILD_KIT_ROOT}/{relative}"
            _safe_build_kit_member(member)
            info = zipfile.ZipInfo(member, FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if member in BUILD_KIT_EXECUTABLE_MEMBERS else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_build_kit_zip() -> None:
    """Build in same-filesystem staging and promote only after every gate passes."""
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    output = DOWNLOADS / BUILD_KIT_NAME
    handle, candidate_name = tempfile.mkstemp(prefix=f".{BUILD_KIT_NAME}.", suffix=".candidate", dir=DOWNLOADS)
    os.close(handle)
    candidate = Path(candidate_name)
    try:
        _write_build_kit_zip(candidate)
        validate_build_kit_zip_structure(candidate)
        run_bundled_build_kit_verifier(candidate)
        os.replace(candidate, output)
    finally:
        candidate.unlink(missing_ok=True)


def run_bundled_build_kit_verifier(zip_path: Path | None = None) -> None:
    """Run only the pinned tracked verifier source, never code loaded from the ZIP."""
    package = BUILD_KIT_SOURCE / BUILD_KIT_ROOT
    verifier = package / "tools" / "verify-build-kit.py"
    if not verifier.is_file():
        raise ValueError("Tracked BREATHE build-kit source missing bundled verifier")
    if sha256(verifier) != BUILD_KIT_VERIFIER_SHA256:
        raise ValueError("BREATHE tracked bundled verifier bytes changed")
    completed = subprocess.run(
        [sys.executable, str(verifier), "--package", str(package), "--zip", str(zip_path or DOWNLOADS / BUILD_KIT_NAME)],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"Bundled BREATHE build-kit verifier failed:\n{completed.stdout[-4000:]}")
    if "VERIFIED BREATHE RESPIRATORY CARE BUILD KIT" not in completed.stdout:
        raise ValueError("Bundled BREATHE verifier did not emit the expected verification summary")


def _ledger_records(text: str, expected: set[str], label: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\\]+)", line)
        if not match:
            raise ValueError(f"Malformed BREATHE {label} checksum line {line_number}")
        relative = Path(match.group(2))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"Unsafe BREATHE {label} checksum path: {relative}")
        name = relative.as_posix()
        if name in records:
            raise ValueError(f"Duplicate BREATHE {label} checksum path: {name}")
        records[name] = match.group(1)
    if set(records) != expected:
        raise ValueError(f"BREATHE {label} checksum inventory mismatch")
    return records


def validate_build_kit_zip_structure(path: Path, *, enforce_pins: bool = True) -> dict:
    """Validate all untrusted metadata before CRC or archive payload reads."""
    if not path.is_file():
        raise ValueError(f"Missing BREATHE build kit: {path}")
    if enforce_pins and (path.stat().st_size != BUILD_KIT_BYTES or sha256(path) != BUILD_KIT_SHA256):
        raise ValueError("BREATHE build kit bytes changed")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if enforce_pins and len(infos) != BUILD_KIT_MEMBERS:
            raise ValueError(f"BREATHE build kit member count changed: {len(infos)}")
        if len(infos) > BUILD_KIT_MEMBERS:
            raise ValueError(f"BREATHE build kit exceeds member limit: {len(infos)}")

        seen: set[str] = set()
        normalized: set[str] = set()
        roots: set[str] = set()
        expanded_bytes = 0
        for info in infos:
            name = info.filename
            raw_name = getattr(info, "orig_filename", name)
            if "\x00" in raw_name or raw_name != name:
                raise ValueError(f"BREATHE build-kit ZIP raw/normalized path mismatch: {raw_name!r}")
            _safe_build_kit_member(name)
            if name in seen:
                raise ValueError(f"Duplicate BREATHE build-kit ZIP member: {name}")
            seen.add(name)
            key = unicodedata.normalize("NFC", name).casefold()
            if key in normalized:
                raise ValueError(f"Case/Unicode-colliding BREATHE build-kit ZIP member: {name}")
            normalized.add(key)
            roots.add(name.split("/", 1)[0])
            if info.flag_bits & 1:
                raise ValueError(f"Encrypted BREATHE build-kit ZIP member is forbidden: {name}")
            if info.compress_type not in BUILD_KIT_ALLOWED_COMPRESSION:
                raise ValueError(f"BREATHE build-kit ZIP compression method is forbidden: {name}")
            if info.is_dir():
                raise ValueError(f"BREATHE build-kit ZIP directory entry is forbidden: {name}")
            mode = (info.external_attr >> 16) & 0o177777
            expected_mode = stat.S_IFREG | (0o755 if name in BUILD_KIT_EXECUTABLE_MEMBERS else 0o644)
            if mode != expected_mode:
                raise ValueError(
                    f"BREATHE build-kit ZIP mode mismatch: {name} "
                    f"expected={oct(expected_mode)} actual={oct(mode)}"
                )
            if info.file_size > BUILD_KIT_MAX_MEMBER_BYTES:
                raise ValueError(f"BREATHE build-kit ZIP member exceeds byte limit: {name}")
            expanded_bytes += info.file_size
            if expanded_bytes > BUILD_KIT_MAX_EXPANDED_BYTES:
                raise ValueError("BREATHE build-kit ZIP exceeds expanded-byte limit")

        if roots != {BUILD_KIT_ROOT}:
            raise ValueError(f"BREATHE build kit root mismatch: {sorted(roots)}")
        for name in seen:
            parts = name.split("/")
            for index in range(1, len(parts)):
                if "/".join(parts[:index]) in seen:
                    raise ValueError(f"BREATHE build-kit ZIP file/directory collision: {name}")
        if enforce_pins and not BUILD_KIT_EXECUTABLE_MEMBERS.issubset(seen):
            raise ValueError("BREATHE build kit missing required executable member")

        # CRC verification reads payloads, so it must follow the complete metadata pass.
        if archive.testzip() is not None:
            raise ValueError("BREATHE build kit ZIP CRC check failed")

        required = {
            f"{BUILD_KIT_ROOT}/README-FIRST.md",
            f"{BUILD_KIT_ROOT}/GIVE-THIS-PACKAGE-TO-HERMES.md",
            f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json",
            f"{BUILD_KIT_ROOT}/SHA256SUMS.txt",
            f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py",
        }
        if not required.issubset(seen):
            raise ValueError("BREATHE build kit missing required handoff, manifest, checksum, or verifier files")

        root_prefix = f"{BUILD_KIT_ROOT}/"
        actual_files = {name.removeprefix(root_prefix) for name in seen}
        manifest = json.loads(archive.read(f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json"))
        inventory = manifest.get("files_excluding_manifest_and_checksums")
        if not isinstance(inventory, list):
            raise ValueError("BREATHE build-kit manifest inventory missing")
        declared: dict[str, dict] = {}
        for record in inventory:
            if not isinstance(record, dict):
                raise ValueError("BREATHE build-kit manifest inventory record is invalid")
            relative = record.get("path")
            if not isinstance(relative, str) or relative in declared:
                raise ValueError(f"BREATHE build-kit manifest inventory path invalid: {relative!r}")
            _safe_build_kit_member(relative)
            if relative in {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}:
                raise ValueError(f"BREATHE build-kit manifest inventory includes generated file: {relative}")
            if not isinstance(record.get("bytes"), int) or record["bytes"] < 0:
                raise ValueError(f"BREATHE build-kit manifest byte count invalid: {relative}")
            if not isinstance(record.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
                raise ValueError(f"BREATHE build-kit manifest digest invalid: {relative}")
            declared[relative] = record
        if set(declared) != actual_files - {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}:
            raise ValueError("BREATHE build-kit manifest inventory does not match archive members")

        verifier_bytes = archive.read(f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py")
        if hashlib.sha256(verifier_bytes).hexdigest() != BUILD_KIT_VERIFIER_SHA256:
            raise ValueError("BREATHE bundled verifier bytes changed")
        expected_ledger = actual_files - {"SHA256SUMS.txt"}
        ledger = _ledger_records(
            archive.read(f"{BUILD_KIT_ROOT}/SHA256SUMS.txt").decode("utf-8"),
            expected_ledger,
            "build-kit",
        )
        for name, digest in ledger.items():
            payload = archive.read(f"{BUILD_KIT_ROOT}/{name}")
            actual_digest = hashlib.sha256(payload).hexdigest()
            if actual_digest != digest:
                raise ValueError(f"BREATHE build-kit checksum mismatch: {name}")
            if name in declared and (
                declared[name]["sha256"] != actual_digest or declared[name]["bytes"] != len(payload)
            ):
                raise ValueError(f"BREATHE build-kit manifest byte/hash mismatch: {name}")
    return manifest


def validate_build_kit() -> dict:
    path = DOWNLOADS / BUILD_KIT_NAME
    manifest = validate_build_kit_zip_structure(path)
    run_bundled_build_kit_verifier()
    if manifest["target"] != {
        "foundation_namespace": "resp_breathe.*",
        "home": "My BREATHE",
        "lane": "respiratory_care",
        "namespace": "resp_breathe.*",
        "product": "BREATHE — Respiratory Care Complete AI OS Mission Control",
        "product_id": "respiratory-care-breathe-mission-control",
        "readiness": "not_operational_build_required",
        "route": "/respiratory-care",
        "version": "2.0.0",
    }:
        raise ValueError("BREATHE build kit target contract changed")
    expected_counts = {
        "agents": 10,
        "canonical_assurance_checks": 160,
        "capability_criteria_including_capstone": 77,
        "capability_domains": 17,
        "control_matrix_rows": 216,
        "core_launchers": 4,
        "cross_cutting_full_stack_scenarios": 48,
        "deployment_contexts": 2,
        "mastery_levels": 4,
        "operational_partitions": 9,
        "protected_workspaces": 5,
        "record_schemas": 18,
        "role_lane": 1,
        "superpowers": 24,
        "task_hats": 7,
        "templates": 30,
        "total_required_execution_records": 424,
        "workflows": 24,
    }
    for key, value in expected_counts.items():
        if manifest["counts"].get(key) != value:
            raise ValueError(f"BREATHE build kit count changed: {key}")
    if manifest["defaults"] != {
        "agents": "PERM-P0 Disabled",
        "external_actions": "Off",
        "memory": "session_only",
        "optional_fifth_launcher": "Empty",
        "perm_p5": "Prohibited",
        "personal_perm_p4": "Unavailable",
        "powers": "Available Inactive",
        "workflows": "Preview Only",
    }:
        raise ValueError("BREATHE build kit defaults changed")
    return manifest


def build() -> dict:
    manifest = validate_package()
    refresh_ledger()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    build_build_kit_zip()
    build_kit_manifest = validate_build_kit()
    output = DOWNLOADS / ZIP_NAME
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(EXPECTED_FILES):
            path = PACKAGE / name
            info = zipfile.ZipInfo(f"{ZIP_PREFIX}/{name}", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    source_record = {
        "acceptance_tests": manifest["acceptance_tests"],
        "activation": manifest["activation"],
        "artifact_class": "legacy_complete_edition_source_package",
        "breathe_overlay_second": True,
        "bytes": output.stat().st_size,
        "device_control": False,
        "device_data_private_use": False,
        "download": f"downloads/{ZIP_NAME}",
        "foundation_first": True,
        "install_on_download": False,
        "installation_status": "not_installed",
        "institutional_deployment_requires_separate_authorization": True,
        "medical_resident_population_state_shared": False,
        "no_phi": True,
        "nursing_population_state_shared": False,
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 24,
        "package_version": manifest["package_version"],
        "population_lane": manifest["population_lane"],
        "pre_install_disclosure_required": True,
        "profession": manifest["profession"],
        "records_total": 18,
        "route": manifest["route"],
        "sha256": sha256(output),
        "standalone_non_nurse_lane": True,
        "suggested_agents_active_after_install": 0,
        "suggested_agents_total": 10,
        "templates_total": 30,
        "workflows_total": 24,
    }
    build_kit_record = {
        "activation_available": True,
        "activation_contract": "user_initiated_read_only_preflight_then_exact_implementation_activation_card_approval",
        "artifact_class": "hermes_functional_build_kit_self_install",
        "bytes": BUILD_KIT_BYTES,
        "build_kit_version": "1.0.0",
        "complete_ai_os_claim": "not_operational_build_required",
        "download": f"downloads/{BUILD_KIT_NAME}",
        "install_on_download": False,
        "institutional_authorization": False,
        "operational_data_authorized": False,
        "population_lane": "respiratory_care",
        "pre_install_disclosure_required": True,
        "readiness": build_kit_manifest["target"]["readiness"],
        "route": "/respiratory-care/",
        "runtime_status": "not_built_until_user_hermes_runs_approved_program",
        "sha256": BUILD_KIT_SHA256,
        "target_application_version": build_kit_manifest["target"]["version"],
        "total_required_execution_records": build_kit_manifest["counts"]["total_required_execution_records"],
    }
    public = {
        "installation_status": "not_installed",
        "packages": [source_record, build_kit_record],
        "purpose": "standalone adjacent clinical lane for respiratory care professionals; separate from Nurse AI OS and Medical Resident ROUNDS; includes verified self-install Hermes build kit",
        "release": manifest["package_version"],
        "release_posture": "source_package_available_build_kit_available_runtime_not_operational_until_user_approved_build",
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(
        f"{source_record['sha256']}  {ZIP_NAME}\n{BUILD_KIT_SHA256}  {BUILD_KIT_NAME}\n",
        encoding="utf-8",
    )
    print("BREATHE_PACKAGES=1")
    print("BREATHE_BUILD_KIT_PACKAGES=1")
    print("INSTALLATION_STATUS=not_installed")
    print(f"BREATHE_ZIP_SHA256={source_record['sha256']}")
    print(f"BREATHE_ZIP_BYTES={source_record['bytes']}")
    print(f"BREATHE_BUILD_KIT_SHA256={BUILD_KIT_SHA256}")
    print(f"BREATHE_BUILD_KIT_BYTES={BUILD_KIT_BYTES}")
    return build_kit_record


def main() -> int:
    try:
        build()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
