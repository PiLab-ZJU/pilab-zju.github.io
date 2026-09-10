### google scholar

- 蒋卓人 https://scholar.google.com/citations?user=GNkq4n8AAAAJ&hl=en
- 言鹏韦 https://scholar.google.com/citations?user=mSSHaM0AAAAJ&hl=en
- 林田谦谨 https://scholar.google.com/citations?hl=en&user=8ItcqywAAAAJ
- 袁伟康 https://scholar.google.com/citations?hl=en&user=I0hMjKwAAAAJ

### Crossref（自动同步用）

完整英文姓名已与现有论文作者表核对；同步时结合 ORCID 与已知合作者消歧，排除同名作者。
脚本读取 Scholar 公开论文列表，以 Crossref 补全出版方书目信息；Crossref 未覆盖的论文再读取 Scholar 详情。也支持 Scholar CSV 导出补充，操作见 [论文同步说明](paper-sync.md)。

- 蒋卓人 https://api.crossref.org/works?query.author=Zhuoren%20Jiang
- 言鹏韦 https://api.crossref.org/works?query.author=Pengwei%20Yan
- 林田谦谨 https://api.crossref.org/works?query.author=Tianqianjin%20Lin
- 袁伟康 https://api.crossref.org/works?query.author=Weikang%20Yuan

### 作者身份校验

以下 ORCID 与现有论文的出版方元数据核对；合作者来自已核实的团队论文。Crossref 候选记录必须匹配完整姓名，并匹配 ORCID、Scholar 列表中的题名或至少一位这里列出的合作者；出现相冲突的 ORCID 时不收录。没有足够身份依据的候选记入同步报告，供人工核对。新增人员可以先只填写 Scholar 地址，无需猜测 ORCID。

```yaml
identities:
  蒋卓人:
    orcid: 0000-0001-8562-8347
    coauthors: [Xiaozhong Liu, Kaisong Song, Kun Kuang, Tianqianjin Lin, Weikang Yuan, Pengwei Yan, Guoxiu He, Johan Bollen, Chenxi Lin]
  言鹏韦:
    orcid: 0009-0000-9139-3652
    coauthors: [Zhuoren Jiang, Tianqianjin Lin, Xiaozhong Liu, Kaisong Song]
  林田谦谨:
    orcid: 0000-0002-4272-394X
    coauthors: [Zhuoren Jiang, Pengwei Yan, Xiaozhong Liu, Kaisong Song, Xurui Li]
  袁伟康:
    orcid: 0000-0001-6047-7036
    coauthors: [Zhuoren Jiang, Tianqianjin Lin, Xiaozhong Liu, Kaisong Song, Chenxi Lin]
```
