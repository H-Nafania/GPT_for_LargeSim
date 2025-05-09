from profile_generator.profile_generator import ProfileGenerator

# default_temperature 毎回同じ結果(0.0~0.2)、一貫性>多様性(0.3~0.5)、一貫性<多様性(0.6~0.9)、創造的で意外性が高い(1.0~)

def test1():
    from pprint import pprint
    excel_file = r"F:\GPT_for_LargeSim\prefile_list.xlsx"

    # ProfileGenerator インスタンス生成時にデフォルト温度を指定可能にする
    # default_temperature 毎回同じ結果(0.0~0.2)、一貫性>多様性(0.3~0.5)、一貫性<多様性(0.6~0.9)、創造的で意外性が高い(1.0~)
    generator = ProfileGenerator(excel_file, default_temperature=0.7)

    names = ["太郎", "花子", "次郎"]
    # generate_profiles 呼び出しで temperature を指定
    profiles = generator.generate_profiles(names, batch_size=1)
    pprint(profiles)
    generator.reform_profile(profiles)
    pprint(generator.df_dict)

def test2(profile_count:int=1000, temperature=0.5, batch_size=10):
    from pprint import pprint
    import uuid
    names = [str(uuid.uuid4()) for _ in range(profile_count)]

    excel_file = r"F:\GPT_for_LargeSim\prefile_list.xlsx"

    export_path = r"F:\GPT_for_LargeSim\profiles\blood_more"

    generator = ProfileGenerator(excel_file, default_temperature=temperature)

    # generate_profiles 呼び出しで temperature を指定
    profiles = generator.generate_profiles(names, batch_size=batch_size)
    # pprint(profiles)
    generator.reform_profile(profiles)
    pprint(generator.df_profile)

    generator.export_profile(export_path)

if __name__ == "__main__":
    import time

    t1 = time.time()
    # test1()
    test2()

    print(f"{time.time()-t1:.2f}")
