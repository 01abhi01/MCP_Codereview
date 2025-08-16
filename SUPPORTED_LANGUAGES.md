# Supported Programming Languages

## Currently Implemented Analysis (Full Support)

### 🐍 **Python** - Complete Analysis
- **Security**: Bandit integration, hardcoded secrets, dangerous functions
- **Quality**: AST analysis, PEP8 style, function complexity
- **Performance**: Loop optimization, list comprehensions
- **Tools**: bandit, pylint, flake8

### 🟨 **JavaScript/TypeScript** - Complete Analysis  
- **Security**: XSS patterns, eval usage
- **Quality**: console.log detection, var usage, equality checks
- **Performance**: DOM queries, array methods optimization
- **Tools**: eslint, jshint

### ☕ **Java** - Complete Analysis
- **Security**: SQL injection patterns, unsafe operations
- **Quality**: System.out.println, empty catch blocks
- **Performance**: Collection usage patterns
- **Tools**: checkstyle, spotbugs

### 📄 **YAML/Ansible** - Complete Analysis (Recently Added)
- **Security**: Hardcoded secrets, shell injection, file permissions
- **Quality**: Deprecated syntax, documentation, formatting
- **Performance**: Module efficiency, loop optimization
- **Tools**: ansible-lint, yamllint

## Partially Supported Languages (Basic Pattern Analysis)

### 🔧 **Go**
- **Detection**: File extension support
- **Tools**: gofmt, golint (if available)
- **Analysis**: Basic pattern matching

### 🦀 **Rust** 
- **Detection**: .rs files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 🅒 **C/C++**
- **Detection**: Multiple extensions (.c, .cpp, .hpp, etc.)
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 🔷 **C#**
- **Detection**: .cs files recognized  
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 🐘 **PHP**
- **Detection**: .php files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 💎 **Ruby**
- **Detection**: .rb files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 🏎️ **Swift**
- **Detection**: .swift files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 🎯 **Kotlin**
- **Detection**: .kt files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 📊 **Scala**
- **Detection**: .scala files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

### 📈 **R**
- **Detection**: .r, .R files recognized
- **Analysis**: Basic pattern matching
- **Tools**: None integrated yet

## Markup & Configuration Languages (Recognition Only)

### 💾 **SQL**
- **Detection**: .sql files recognized
- **Analysis**: Basic SQL injection pattern detection

### 🐚 **Shell Scripts**
- **Bash**: .sh files recognized
- **PowerShell**: .ps1 files recognized
- **Analysis**: Basic pattern matching

### 📝 **Markup Languages**
- **JSON**: .json files recognized
- **XML**: .xml files recognized  
- **HTML**: .html, .htm files recognized
- **CSS**: .css files recognized
- **SCSS**: .scss files recognized
- **Less**: .less files recognized

## Analysis Capabilities Summary

| Language | Security | Quality | Performance | Tools | Status |
|----------|----------|---------|-------------|-------|---------|
| Python | ✅ | ✅ | ✅ | 3 tools | Complete |
| JavaScript/TypeScript | ✅ | ✅ | ✅ | 2 tools | Complete |
| Java | ✅ | ✅ | ✅ | 2 tools | Complete |
| YAML/Ansible | ✅ | ✅ | ✅ | 2 tools | Complete |
| Go | ⚠️ | ⚠️ | ⚠️ | 2 tools | Basic |
| Others | ⚠️ | ⚠️ | ⚠️ | 0 tools | Recognition |

**Total Supported**: 26+ languages
**Fully Implemented**: 4 languages (Python, JS/TS, Java, YAML/Ansible)
**Basic Support**: 22+ languages

## Adding New Language Support

To add full analysis for a new language:

1. **Add analysis methods**: `_analyze_[lang]_quality()`, `_analyze_[lang]_performance()`
2. **Add tool integration**: `_run_[tool]()` method
3. **Update language routing**: Add to quality/performance analysis conditions
4. **Add security patterns**: Language-specific security checks
5. **Test thoroughly**: Create test cases and validate results
