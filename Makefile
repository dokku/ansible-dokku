.PHONY: clean
clean:
	rm -f README.md defaults/main.yml ../dokku.tar.gz

.PHONY: release
release: generate
	cd .. && tar -zcvf dokku-$(shell cat meta/main.yml | grep version | head -n 1 | cut -d':' -f2 | xargs).tar.gz dokku

.PHONY: generate
generate: clean README.md defaults/main.yml ansible-role-requirements.yml

.PHONY: README.md
README.md:
	bin/generate

.PHONY: defaults/main.yml
defaults/main.yml:
	bin/generate

.PHONY: ansible-role-requirements.yml
ansible-role-requirements.yml:
	bin/generate
