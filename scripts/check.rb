require "jekyll"
require "tmpdir"
require "cgi"

SOURCE = File.expand_path("..", __dir__)

def assert(condition, message)
  raise message unless condition
end

def build(destination, baseurl = "")
  config = Jekyll.configuration("source" => SOURCE, "destination" => destination,
    "baseurl" => baseurl, "url" => "", "disable_disk_cache" => true, "quiet" => true)
  site = Jekyll::Site.new(config)
  site.reset
  site.read
  yield site if block_given?
  site.generate
  site.render
  site.cleanup
  site.write
  assert(system("python3", File.join(__dir__, "check_html.py"), destination, baseurl), "HTML validation failed")
  site
end

Dir.mktmpdir("pilab-check-") do |directory|
  production = File.join(directory, "production")
  site = build(production)
  # A draft must not leave a publicly addressable detail page behind.
  Dir.glob(File.join(SOURCE, "_papers", "*.md")).each do |path|
    metadata = YAML.safe_load(File.read(path).split(/^---\s*$\n?/)[1], permitted_classes: [Date, Time])
    next unless metadata["published"] == false
    slug = File.basename(path, ".md")
    assert(!File.exist?(File.join(production, "papers", slug, "index.html")), "Draft paper was emitted: #{slug}")
  end
  public_papers = site.collections["papers"].docs.reject { |p| p.data["published"] == false }
  public_papers.each do |paper|
    assert(paper.data["authors"].is_a?(Array) && !paper.data["authors"].empty?, "Missing authors: #{paper.basename}")
    assert(paper.data["links"].to_a.any? { |link| link["url"].to_s.start_with?("https://doi.org/", "https://scholar.google.com/citations?") }, "Missing DOI or Scholar source link: #{paper.basename}")
  end
  team_page = File.read(File.join(production, "team/index.html"))
  site.data.fetch("people_sources", {}).each do |name, sources|
    active_names = [site.data["team"]["advisor"], *%w[students partners postdocs].flat_map { |section| site.data["team"].fetch(section, []) }].reject { |m| m["published"] == false }.map { |m| m["name"] }
    next unless sources["scholar"] && active_names.include?(name)
    assert(team_page.include?(CGI.escapeHTML(sources["scholar"])), "Missing Scholar link: #{name}")
  end
  %w[students partners postdocs alumni].each do |section|
    site.data["team"].fetch(section, []).each do |member|
      next if member["published"] == false
      assert(team_page.include?(CGI.escapeHTML(member["name"])), "Missing team member: #{member['name']}")
      if member["role"]
        assert(team_page.include?(CGI.escapeHTML(member["role"])), "Missing team role: #{member['name']}")
      end
    end
  end

  alumni_html = team_page.split('<div class="alumni-list">', 2).last.split('<!-- ============ 加入我们', 2).first
  assert(!alumni_html.include?('<a '), "Alumni personal links must be hidden")
  site.data["team"].fetch("alumni", []).each do |member|
    next if member["published"] == false || member["photo"].to_s.strip.empty?
    assert(alumni_html.include?("src=\"#{member['photo']}\""), "Missing alumni photo: #{member['name']}")
  end
  site.data["team"]["students"].group_by { |m| m["degree"] }.each_value do |members|
    dated = members.reject { |m| m["published"] == false || !m["year"] }.sort_by { |m| -m["year"] }
    positions = dated.map { |m| team_page.index(CGI.escapeHTML(m["name"])) }
    assert(positions == positions.sort, "Students must be newest first")
  end

  ["", "/qa"].each_with_index do |baseurl, index|
    destination = File.join(directory, "fixture#{index}")
    build(destination, baseurl) do |fixture|
      fixture.data["projects"]["github"] += [
        {"name" => "QA A | B + 中文", "date" => "2099-09", "url" => "/team/"},
        {"name" => "QA_DAY", "date" => "2099-09-02", "url" => "https://example.com/?q=a%7Cb"},
        {"name" => "QA_HIDDEN_PROJECT", "date" => "2099-10", "url" => "/missing/", "published" => false}
      ]
      fixture.data["team"]["students"] = [
        {"name" => "甲_缺省照片", "degree" => "博士研究生"}, {"name" => "乙_空照片", "photo" => "", "degree" => "博士研究生"},
        {"name" => "丙_空格照片", "photo" => "  ", "degree" => "硕士研究生"},
        {"name" => "丁_有效照片", "photo" => "/assets/img/team/advisor.jpg", "degree" => "硕士研究生"},
        {"name" => "QA_HIDDEN_STUDENT", "published" => false, "degree" => "隐藏分组"}
      ]
      fixture.data["team"]["partners"] += [{"name" => "QA_HIDDEN_PARTNER", "published" => false}]
      fixture.data["team"]["alumni"] += [{"name" => "QA_HIDDEN_ALUMNUS", "published" => false, "grad" => "2099.06"}]
      # Exercise the rolling year boundary independently of real publications.
      fixture.collections["papers"].docs.each { |paper| paper.data["date"] = Time.utc(fixture.time.year - 4, 1, 1) }
      [["QA_OLD_PAPER", -3], ["QA_FUTURE_PAPER", 1], ["QA_YEAR_PAPER", 0]].each_with_index do |(title, offset), position|
        paper = fixture.collections["papers"].docs[position]
        paper.data.merge!("title" => title, "date" => Time.utc(fixture.time.year + offset, 1, 1),
          "date_precision" => "year", "published" => true)
      end
    end
    home = CGI.unescapeHTML(File.read(File.join(destination, "index.html")))
    projects = File.read(File.join(destination, "projects/index.html"))
    team = File.read(File.join(destination, "team/index.html"))
    papers = File.read(File.join(destination, "papers/index.html"))
    %w[QA_OLD_PAPER QA_FUTURE_PAPER].each do |title|
      assert(!home.include?(title) && !papers.include?(title), "Paper outside three-year window leaked: #{title}")
    end
    assert(papers.include?("QA_YEAR_PAPER"), "Current-year paper missing")
    assert(home.include?("datetime=\"#{site.time.year}\""), "Year-only paper date precision lost")
    assert(home.include?("QA A | B + 中文"), "Special characters damaged recent entries")
    assert(home.index("QA_DAY") < home.index("QA A | B + 中文"), "Month/day sorting failed")
    assert(home.include?('datetime="2099-09"') && home.include?('datetime="2099-09-02"'), "Date precision lost")
    assert(home.include?("href=\"#{baseurl}/team/#join\"") && home.include?("href=\"#{baseurl}/team/\""), "Internal baseurl links failed")
    assert(home.include?('href="https://example.com/?q=a%7Cb"'), "External URL changed")
    assert(!home.include?("QA_HIDDEN") && !projects.include?("QA_HIDDEN") && !team.include?("QA_HIDDEN"), "Draft content leaked")
    assert(team.include?("PhD Students · 2") && team.include?("Master’s Students · 2"), "Student group counts failed")
    assert(!team.include?("隐藏分组"), "Empty draft student group leaked")
    %w[甲 乙 丙].each { |initial| assert(team.match?(/<span[^>]*>#{initial}<\/span>/), "Missing avatar fallback: #{initial}") }
    assert(team.include?("src=\"#{baseurl}/assets/img/team/advisor.jpg\" alt=\"丁_有效照片\""), "Valid avatar missing")
  end
end
puts "PASS: team members and Scholar links, publication metadata, three-year window, draft exclusion, avatars, aggregation, date precision and deployment paths"
