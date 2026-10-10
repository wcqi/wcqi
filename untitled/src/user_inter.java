import java.util.Scanner;

public class user_inter {
    public  static void main(String args[]) {
        Scanner sc = new Scanner(System.in);

        System.out.println("请输入你的名字：");
        String name = sc.next();

        System.out.println("请输入你的分数：");
        int score = sc.nextInt();

        if (score >= 60) {
            System.out.println(name + ",你及格了！");
        }else  {
            System.out.println(name + ",再接再励！");
        }
    }
}
