.PHONY: clean
clean:
	rm -f README.md defaults/main.yml ../dokku.tar.gz

.PHONY: release
release: generate
	cd .. && tar -zcvf dokku-$(shell cat meta/main.yml | grep version | head -n 1 | cut -d':' -f2 | xargs).tar.gz dokku

.PHONY: generate
generate: README.md defaults/main.yml

README.md:
	bin/generate

defaults/main.yml:
	bin/generate
