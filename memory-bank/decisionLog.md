# Decision Log

## Technical Decisions

### Initial Project Structure (2025-05-28)
Initialized Unknown with a modular architecture using Node.js

**Status:** accepted
**Impact:** Project-wide

Rationale:
Established foundation for scalable and maintainable development




### Development Workflow (2025-05-28)
Established initial development workflow and practices

**Status:** accepted
**Impact:** Development process

Rationale:
Ensure consistent development process and code quality

Alternatives Considered:
- Ad-hoc development process
- Waterfall methodology



### Documentation Strategy (2025-05-28)
Implemented automated documentation with memory bank

**Status:** accepted
**Impact:** Project documentation

Rationale:
Maintain up-to-date project context and decision history

### ユーティリティ関数の活用 (2025-05-28)
src/image/collector.py内の独自処理をユーティリティ関数に置き換え

**Status:** accepted
**Impact:** コード品質と保守性の向上

Rationale:
コードの重複を減らし、共通のユーティリティ関数を使用することで一貫性を向上させるため。また、将来ユーティリティ関数が改善された場合に、自動的にその恩恵を受けることができる。

Alternatives Considered:
- 独自処理を維持する
- ユーティリティ関数を新たに作成する

### 新規追加ディレクトリのみを処理する機能の実装 (2025-05-28)
image_collector.pyに新規追加ディレクトリのみを処理する機能を実装し、処理済みディレクトリを記録するための仕組みを導入した。

**Status:** accepted
**Impact:** 画像収集プロセスの効率化、Google API使用量の削減

Rationale:
baseディレクトリに新しく追加された人物ディレクトリのみを処理することで、既に処理済みのディレクトリを再処理する無駄を省き、効率的に画像収集を行えるようにするため。

Alternatives Considered:
- すべてのディレクトリを毎回処理する（従来の方法）
- データベースで処理済みディレクトリを管理する
- ファイルのタイムスタンプで新規追加を判断する

## Pending Decisions
