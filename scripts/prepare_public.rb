require "date"
require "fileutils"
require "yaml"

source = File.expand_path("..", __dir__)
abort "Usage: ruby scripts/prepare_public.rb EMPTY_DESTINATION" unless ARGV.size == 1
destination = File.expand_path(ARGV.first)
abort "Destination must be outside the source directory" if destination == source || destination.start_with?(source + File::SEPARATOR)
abort "Destination must be an empty directory" if File.exist?(destination) && (!File.directory?(destination) || !Dir.empty?(destination))
FileUtils.mkdir_p(destination)

def public_data(value)
  case value
  when Array
    value.reject { |entry| entry.is_a?(Hash) && entry["published"] == false }.map { |entry| public_data(entry) }
  when Hash
    value.transform_values { |entry| public_data(entry) }
  else
    value
  end
end

files = %w[
  .gitignore .ruby-version Gemfile Gemfile.lock README.md _config.yml
  index.html 404.html team/index.html news/index.html papers/index.html projects/index.html
  docs/github-pages-deployment-plan.md docs/fix-assets-2026-09-09/asset-sources.json
  docs/design-review-2026-09-10.md
]
%w[.github _includes _layouts assets scripts].each do |directory|
  files.concat(Dir.glob(File.join(source, directory, "**", "*"), File::FNM_DOTMATCH)
    .select { |path| File.file?(path) }
    .map { |path| path.delete_prefix(source + File::SEPARATOR) })
end
files.reject! { |path| File.basename(path).start_with?(".") && path != ".gitignore" && path != ".ruby-version" }
files.delete("assets/img/logo-preview.html")

%w[_papers _news].each do |collection|
  Dir.glob(File.join(source, collection, "*.md")).each do |path|
    metadata = YAML.safe_load(File.read(path).split(/^---\s*$\n?/)[1], permitted_classes: [Date, Time]) || {}
    files << path.delete_prefix(source + File::SEPARATOR) unless metadata["published"] == false
  end
end

files.sort.each do |relative|
  target = File.join(destination, relative)
  FileUtils.mkdir_p(File.dirname(target))
  FileUtils.cp(File.join(source, relative), target)
end

FileUtils.mkdir_p(File.join(destination, "_data"))
Dir.glob(File.join(source, "_data", "*.yml")).each do |path|
  data = YAML.safe_load_file(path, permitted_classes: [Date, Time])
  File.write(File.join(destination, "_data", File.basename(path)), YAML.dump(public_data(data)))
end

puts "Prepared public source at #{destination}"
puts "Unpublished collection entries and data records were excluded; local originals were preserved."
