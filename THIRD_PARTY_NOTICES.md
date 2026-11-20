# Third-party verification tools

This repository's verification scripts obtain external proof checkers from
upstream repositories at fixed Git revisions. **No upstream source code or
compiled binary is included in this distribution.** Each dependency remains
subject to its own license.

| Tool | Upstream project and pinned source | Authors and copyright attribution | Upstream license |
| --- | --- | --- | --- |
| DRAT-trim | [marijnheule/drat-trim](https://github.com/marijnheule/drat-trim/tree/effa1dcce85c878236f8313133dff1a2b766cd7c), commit `effa1dcce85c878236f8313133dff1a2b766cd7c` | Marijn Heule and Nathan Wetzler (University of Texas at Austin); other contributors | [MIT](https://github.com/marijnheule/drat-trim/blob/effa1dcce85c878236f8313133dff1a2b766cd7c/LICENSE) |
| CakeML `cake_lpr` | [tanyongkiam/cake_lpr](https://github.com/tanyongkiam/cake_lpr/tree/033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2), commit `033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2` | Marijn Heule, Magnus Myreen, Yong Kiam Tan; CakeML contributors | [CakeML three-clause BSD-style license and notices](https://github.com/tanyongkiam/cake_lpr/blob/033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2/LICENSE) |

The included build scripts pin the Git revisions above. The checkers are
retrieved at reproduction time, not redistributed or relicensed by this work.
Follow the upstream licenses and required copyright notices when redistributing
the external software separately.
