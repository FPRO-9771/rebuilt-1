# Team 9771 FPRO -- Quick Reference

**Tape this to the wall. When in doubt, run `./team` for the menu.**

---

## Every Time You Sit Down

```
cd ~/PycharmProjects/rebuilt-1
source .venv/bin/activate
git pull
```

Not sure if your Mac is set up? Run `./team` and pick option **1** (Check my environment).
First time on this Mac? Pick option **2** (Set up my account).

---

## Code (Git)

| What you want to do              | Command                                        |
|----------------------------------|-------------------------------------------------|
| Get the latest code              | `git pull`                                      |
| See what you changed             | `git status`                                    |
| Save + push your changes         | `git add -A` then `git commit -m "message"` then `git push` |
| Undo all your changes (careful!) | `git checkout -- .`                             |

**Can't push or pull?**
1. Check GitHub CLI: `gh --version` -- if not found, ask Brian
2. Log in: `gh auth login` (pick GitHub.com, HTTPS, web browser)

---

## Robot

| What you want to do             | Command                                          |
|---------------------------------|--------------------------------------------------|
| Run tests                       | `python -m pytest tests/ -v`                     |
| Run simulation                  | `python -m robotpy sim`                          |
| Deploy to robot                 | `python -m robotpy deploy`                       |
| Deploy (skip tests, faster)     | `python -m robotpy deploy --skip-tests`          |

**Deploy not working?**
1. Make sure `.venv` is activated (you should see `(.venv)` in your terminal)
2. Make sure you are connected to the robot (USB or WiFi)
3. Try: `python -m robotpy installer download-python`
4. Try: `python -m robotpy installer download -r requirements.txt`
5. Try: `python -m robotpy installer install -r requirements.txt`
6. Still stuck? Ask Brian

---

## Python Virtual Environment

You must activate the virtual environment every time you open a new terminal.

```
source .venv/bin/activate       <-- turn it on  (you'll see (.venv) in your prompt)
deactivate                      <-- turn it off (when you're done)
```

**Wrong Python version or .venv broken?** Run `./team` option **2** to fix it.

---

## Useful Extras

| What                    | Command                          |
|-------------------------|----------------------------------|
| Open Claude Code        | `claude`                         |
| Check Python version    | `python3 --version` (need 3.13) |
| SSH into the robot      | `ssh admin@10.97.71.2`          |
| Watch robot log live    | `tail -f /var/local/natinst/log/FRC_UserProgram.log` (on robot via SSH) |

---

*Run `./team` for the full menu. See `docs/` for detailed guides.*
